import hashlib
from collections.abc import Iterable

from sqlalchemy.orm import Session, joinedload

from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportStatus
from app.schemas.user import (
    UserDashboard,
    UserDashboardAssignedHotel,
    UserDashboardRecommendation,
    UserDashboardRecommendationDate,
)
from app.services import program_hotel_service, report_service


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def update_user_profile(
    db: Session,
    *,
    user: User,
    first_name: str | None = None,
    last_name: str | None = None,
    cities: list[str] | None = None,
    guests: int | None = None,
) -> User:
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if cities is not None:
        user.cities = cities
    if guests is not None:
        user.guests = guests
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _generate_promo_code(user: User) -> str:
    payload = f"{user.id}:{user.email}:{user.created_at.isoformat() if user.created_at else ''}"
    digest = hashlib.sha1(payload.encode("utf-8")).digest()
    letters_part = ''.join(chr(65 + byte % 26) for byte in digest[:5])
    middle_letters = ''.join(chr(65 + byte % 26) for byte in digest[5:7])
    digits = ''.join(str(byte % 10) for byte in digest[7:9])
    return f"{letters_part}-{middle_letters}{digits}"


_STATUS_LABELS = {
    ReportStatus.DRAFT: "Отчет в процессе",
    ReportStatus.ON_MODERATION: "Отчет на модерации",
    ReportStatus.APPROVED: "Отчет одобрен",
    ReportStatus.REJECTED: "Отчет отклонен",
}


def _serialize_recommendations(raw: Iterable[dict]) -> list[UserDashboardRecommendation]:
    recommendations: list[UserDashboardRecommendation] = []
    for item in raw:
        hotel = item.get("hotel")
        if hotel is None:
            continue
        dates = [
            UserDashboardRecommendationDate(
                check_in_date=entry["check_in_date"],
                check_out_date=entry["check_out_date"],
                slots_available=entry["slots_available"],
            )
            for entry in item.get("available_dates", [])
        ]
        recommendations.append(
            UserDashboardRecommendation(
                hotel_id=hotel.id,
                hotel_name=hotel.name,
                city=hotel.city,
                rating=hotel.rating,
                cost=hotel.cost,
                guests=hotel.guests,
                available_dates=dates,
            )
        )
    return recommendations


def get_user_recommendations(
    db: Session,
    *,
    user: User,
    limit: int = 5,
) -> list[UserDashboardRecommendation]:
    raw = program_hotel_service.list_available_program_hotels_with_dates(
        db,
        user=user,
        limit=limit,
    )
    return _serialize_recommendations(raw)


def get_user_dashboard(db: Session, *, user: User) -> UserDashboard:
    promo_code = _generate_promo_code(user)

    report: Report | None = (
        db.query(Report)
        .options(joinedload(Report.hotel))
        .filter(Report.user_id == user.id)
        .order_by(Report.updated_at.desc(), Report.created_at.desc())
        .first()
    )

    participation_status = "Нет активной проверки"
    can_submit_report = False
    assigned_hotel: UserDashboardAssignedHotel | None = None

    if report:
        status_enum = ReportStatus(report.status)
        participation_status = _STATUS_LABELS.get(status_enum, status_enum.value)
        can_submit_report = report_service.editing_enabled(report)

        hotel = report.hotel
        if hotel:
            assigned_hotel = UserDashboardAssignedHotel(
                report_id=report.id,
                hotel_id=hotel.id,
                hotel_name=hotel.name,
                status=status_enum,
                checkout_date=report.checkout_date,
                can_submit=can_submit_report,
            )

        if status_enum != ReportStatus.DRAFT:
            can_submit_report = False

    show_recommendations = assigned_hotel is None or not can_submit_report
    recommendations = get_user_recommendations(db, user=user, limit=5) if show_recommendations else []

    return UserDashboard(
        promo_code=promo_code,
        participation_status=participation_status,
        can_submit_report=can_submit_report,
        assigned_hotel=assigned_hotel,
        recommendations=recommendations,
    )
