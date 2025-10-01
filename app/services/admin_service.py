from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.hotel import Hotel
from app.models.program_application import ProgramApplication, ProgramApplicationStatus
from app.models.report import Photo, Report
from app.models.user import User
from app.schemas.admin import (
    HotelCardReportEntry,
    HotelCardReportList,
    HotelCardReportPhoto,
    ReportModerationRow,
    SecretGuestApplicationRow,
    SecretGuestStatsRow,
)
from app.schemas.report import (
    AmenitiesState,
    FoodAssortment,
    FoodMatch,
    ReportStatus,
    ReportStep1Payload,
    ReportStep2Payload,
    ReportStep6Payload,
    WaitTime,
    WifiQuality,
)
from app.services import application_service


def _full_name(user: User | None) -> str:
    if user is None:
        return ""
    parts = [user.first_name, user.last_name]
    return " ".join(part for part in parts if part).strip() or (user.email or "")


def list_secret_guest_applications(db: Session) -> list[SecretGuestApplicationRow]:
    applications: Iterable[ProgramApplication] = (
        db.query(ProgramApplication)
        .options(joinedload(ProgramApplication.user))
        .filter(ProgramApplication.status == ProgramApplicationStatus.accepted)
        .order_by(ProgramApplication.created_at.desc())
        .all()
    )

    rows: list[SecretGuestApplicationRow] = []
    for application in applications:
        user = application.user
        rows.append(
            SecretGuestApplicationRow(
                application_id=application.id,
                user_id=user.id if user else None,
                full_name=_full_name(user),
                email=user.email if user else None,
                score=application_service.calculate_application_score(application),
                status=application.status,
                submitted_at=application.created_at,
            )
        )
    return rows


def list_secret_guest_stats(db: Session) -> list[SecretGuestStatsRow]:
    query = (
        db.query(
            User,
            func.coalesce(
                func.count(Report.id).filter(Report.status == ReportStatus.APPROVED.value),
                0,
            ).label("reports_count"),
        )
        .outerjoin(Report, Report.user_id == User.id)
        .filter(User.role == "accepted")
        .group_by(User.id)
        .order_by(User.rating.desc(), User.last_name.asc(), User.first_name.asc())
    )

    rows: list[SecretGuestStatsRow] = []
    for user, reports_count in query.all():
        rows.append(
            SecretGuestStatsRow(
                user_id=user.id,
                full_name=_full_name(user),
                email=user.email,
                level=user.rating,
                reports_count=int(reports_count or 0),
            )
        )
    return rows


def list_reports_on_moderation(db: Session) -> list[ReportModerationRow]:
    reports: Iterable[Report] = (
        db.query(Report)
        .options(joinedload(Report.user), joinedload(Report.hotel))
        .filter(Report.status == ReportStatus.ON_MODERATION.value)
        .order_by(Report.submitted_at.desc().nullslast(), Report.updated_at.desc())
        .all()
    )

    rows: list[ReportModerationRow] = []
    for report in reports:
        user = report.user
        hotel = report.hotel
        rows.append(
            ReportModerationRow(
                report_id=report.id,
                user_id=user.id if user else None,
                full_name=_full_name(user),
                level=user.rating if user else None,
                hotel_id=hotel.id if hotel else report.hotel_id,
                hotel_name=hotel.name if hotel else "",
                status=ReportStatus(report.status),
                overall_score=report.overall_score,
                submitted_at=report.submitted_at,
            )
        )
    return rows


_WIFI_DESCRIPTIONS = {
    WifiQuality.STABLE_FAST: "быстрый, никаких проблем",
    WifiQuality.INTERMITTENT: "иногда пропадает",
    WifiQuality.VERY_SLOW: "очень медленный",
    WifiQuality.ABSENT: "нет доступа",
}

_WAIT_TIME_DESCRIPTIONS = {
    WaitTime.INSTANT: "заселение мгновенное",
    WaitTime.UP_TO_10: "ожидание до 10 минут",
    WaitTime.FROM_10_TO_30: "ожидание до 30 минут",
    WaitTime.OVER_30: "ожидание более 30 минут",
}

_FOOD_MATCH_DESCRIPTIONS = {
    FoodMatch.FULL: "соответствует фотографиям",
    FoodMatch.PARTIAL: "частично соответствует",
    FoodMatch.NOT_MATCH: "не соответствует",
}

_AMENITIES_DESCRIPTIONS = {
    AmenitiesState.ALL_WORK: "все удобства в порядке",
    AmenitiesState.SOME_NOT_WORKING: "есть неполадки",
    AmenitiesState.EXTRA_NOT_LISTED: "есть дополнительные удобства",
}

_FOOD_ASSORTMENT_DESCRIPTIONS = {
    FoodAssortment.RICH: "богатый выбор",
    FoodAssortment.STANDARD: "стандартный набор",
    FoodAssortment.MODEST: "скромный выбор",
}


def _score_label(score: float | None) -> str:
    if score is None:
        return "Без оценки"
    if score >= 9.5:
        return "Превосходно"
    if score >= 8.0:
        return "Отлично"
    if score >= 6.5:
        return "Хорошо"
    if score >= 5.0:
        return "Удовлетворительно"
    return "Ниже ожиданий"


def _gather_user_applications(db: Session, user_ids: Iterable[int | None]) -> dict[int, ProgramApplication]:
    clean_ids = {uid for uid in user_ids if uid is not None}
    if not clean_ids:
        return {}
    applications = (
        db.query(ProgramApplication)
        .filter(
            ProgramApplication.user_id.in_(clean_ids),
            ProgramApplication.status == ProgramApplicationStatus.accepted,
        )
        .order_by(ProgramApplication.created_at.desc())
        .all()
    )
    mapping: dict[int, ProgramApplication] = {}
    for application in applications:
        mapping.setdefault(application.user_id, application)
    return mapping


def _build_tags(step1: ReportStep1Payload | None, step2: ReportStep2Payload | None) -> list[str]:
    tags: list[str] = []
    if step2 is not None:
        wifi = _WIFI_DESCRIPTIONS.get(step2.wifi_quality)
        if wifi:
            tags.append(f"Оценка Wi-Fi: {wifi}")
        wait_time = _WAIT_TIME_DESCRIPTIONS.get(step2.wait_time)
        if wait_time:
            tags.append(wait_time)
        food_match = _FOOD_MATCH_DESCRIPTIONS.get(step2.food_match)
        if food_match:
            tags.append(f"Кухня: {food_match}")
        food_assortment = _FOOD_ASSORTMENT_DESCRIPTIONS.get(step2.food_assortment)
        if food_assortment:
            tags.append(f"Завтрак: {food_assortment}")
    if step1 is not None:
        amenities = _AMENITIES_DESCRIPTIONS.get(step1.amenities_state)
        if amenities:
            tags.append(f"Удобства: {amenities}")
    return tags


def _serialize_card_entry(
    report: Report,
    step1: ReportStep1Payload | None,
    step2: ReportStep2Payload | None,
    step6: ReportStep6Payload | None,
    photos: list[Photo],
    application: ProgramApplication | None,
) -> HotelCardReportEntry:
    travel_party = application.travel_party if application else None
    trip_type = None
    if travel_party == "a":
        trip_type = "Отдых, одиночка"
    elif travel_party == "b":
        trip_type = "Отдых, пара"
    elif travel_party == "c":
        trip_type = "Отдых, семья"

    stay_context = None
    if report.checkout_date:
        stay_context = report.checkout_date.strftime("%B %Y")

    base_url = settings.static_url.rstrip('/')
    photo_models = [
        HotelCardReportPhoto(
            id=photo.id,
            url=f'{base_url}/{photo.path}',
            section=photo.section,
        )
        for photo in photos
    ]

    return HotelCardReportEntry(
        report_id=report.id,
        score=report.overall_score,
        score_label=_score_label(report.overall_score),
        submitted_at=report.submitted_at,
        trip_type=trip_type,
        stay_context=stay_context,
        good_text=step6.liked if step6 else None,
        bad_text=step6.to_improve if step6 else None,
        advantages_text=step6.advantages if step6 else None,
        tags=_build_tags(step1, step2),
        photos=photo_models,
    )


def get_hotel_card_reports(
    db: Session,
    *,
    hotel_id: int,
    limit: int | None = None,
) -> HotelCardReportList:
    hotel: Hotel | None = db.get(Hotel, hotel_id)
    if hotel is None:
        raise ValueError("Hotel not found")

    query = (
        db.query(Report)
        .options(joinedload(Report.photos), joinedload(Report.user))
        .filter(
            Report.hotel_id == hotel_id,
            Report.status == ReportStatus.APPROVED.value,
        )
        .order_by(Report.submitted_at.desc().nullslast(), Report.updated_at.desc())
    )
    if limit:
        query = query.limit(limit)

    reports = query.all()
    user_ids = {report.user_id for report in reports if report.user_id is not None}
    applications = _gather_user_applications(db, user_ids)

    scores = [report.overall_score for report in reports if report.overall_score is not None]
    average_score = round(sum(scores) / len(scores), 1) if scores else None

    items: list[HotelCardReportEntry] = []
    for report in reports:
        answers = report.answers or {}
        step1_data = answers.get("step1") if isinstance(answers, dict) else None
        step2_data = answers.get("step2") if isinstance(answers, dict) else None
        step6_data = answers.get("step6") if isinstance(answers, dict) else None

        step1 = None
        if step1_data:
            try:
                step1 = ReportStep1Payload.model_validate(step1_data)
            except Exception:  # noqa: BLE001
                step1 = None
        step2 = None
        if step2_data:
            try:
                step2 = ReportStep2Payload.model_validate(step2_data)
            except Exception:  # noqa: BLE001
                step2 = None
        step6 = None
        if step6_data:
            try:
                step6 = ReportStep6Payload.model_validate(step6_data)
            except Exception:  # noqa: BLE001
                step6 = None

        photos = sorted(report.photos, key=lambda photo: photo.id)
        application = applications.get(report.user_id) if report.user_id else None

        items.append(
            _serialize_card_entry(
                report,
                step1,
                step2,
                step6,
                photos,
                application,
            )
        )

    return HotelCardReportList(
        hotel_id=hotel.id,
        hotel_name=hotel.name,
        total_reports=len(reports),
        average_score=average_score,
        items=items,
    )
