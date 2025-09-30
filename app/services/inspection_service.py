from collections.abc import Sequence

from sqlalchemy.orm import Session, joinedload

from app.models.hotel import Hotel
from app.models.inspection import Inspection, InspectionStatus
from app.models.program_hotel import ProgramHotel
from app.services import program_hotel_service


class InspectionSelectionError(ValueError):
    """Ошибка при выборе отеля для проверки."""


def list_inspections(
    db: Session,
    *,
    guest_id: int | None = None,
    status: InspectionStatus | None = None,
) -> Sequence[Inspection]:
    """Возвращает список проверок с опциональной фильтрацией."""

    query = (
        db.query(Inspection)
        .options(
            joinedload(Inspection.hotel),
            joinedload(Inspection.guest),
            joinedload(Inspection.promocode),
            joinedload(Inspection.report),
        )
        .order_by(Inspection.created_at.desc())
    )

    if guest_id is not None:
        query = query.filter(Inspection.guest_id == guest_id)

    if status is not None:
        query = query.filter(Inspection.status == status)

    return query.all()


def get_inspection(db: Session, inspection_id: int) -> Inspection | None:
    """Возвращает проверку по идентификатору."""

    return (
        db.query(Inspection)
        .options(
            joinedload(Inspection.hotel),
            joinedload(Inspection.guest),
            joinedload(Inspection.promocode),
            joinedload(Inspection.report),
        )
        .filter(Inspection.id == inspection_id)
        .first()
    )


def select_hotel_for_inspection(
    db: Session,
    *,
    hotel_id: int,
    guest_id: int,
    home_city: str | None = None,
    preferred_city: str | None = None,
    guests_count: int = 1,
) -> Inspection:
    """Создает новую проверку для пользователя и уменьшает количество доступных слотов."""

    hotel = db.get(Hotel, hotel_id)
    if hotel is None:
        raise InspectionSelectionError("Отель не найден")

    if not hotel.is_active:
        raise InspectionSelectionError("Отель недоступен для проверки")

    if guests_count <= 0:
        raise InspectionSelectionError("Количество путешественников должно быть положительным")

    is_available_for_user = program_hotel_service.is_hotel_available_for_user(
        db,
        hotel_id=hotel_id,
        home_city=home_city,
        preferred_city=preferred_city,
        guests_count=guests_count,
    )

    if not is_available_for_user:
        raise InspectionSelectionError("Отель недоступен для пользователя")

    program_entry = (
        db.query(ProgramHotel)
        .filter(
            ProgramHotel.hotel_id == hotel_id,
            ProgramHotel.is_published.is_(True),
            ProgramHotel.slots_available >= guests_count,
        )
        .order_by(ProgramHotel.check_in_date.asc())
        .first()
    )

    if program_entry is None:
        raise InspectionSelectionError("Нет доступных слотов для выбранного отеля")

    program_entry.slots_available -= guests_count

    inspection = Inspection(hotel_id=hotel_id, guest_id=guest_id)
    db.add(program_entry)
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection