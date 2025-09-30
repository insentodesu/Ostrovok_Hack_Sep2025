from datetime import datetime
from collections.abc import Sequence

from sqlalchemy.orm import Session, joinedload

from app.models.hotel import Hotel
from app.models.program_hotel import ProgramHotel


class ProgramHotelCreationError(ValueError):
    """Ошибка при добавлении слотов для отеля в программу."""

class ProgramHotelSelectionError(ValueError):
    """Ошибка при подборе отелей для секретного гостя."""

def create_program_hotel(
    db: Session,
    *,
    hotel_id: int,
    check_in_date: datetime,
    check_out_date: datetime,
    slots_total: int = 1,
    slots_available: int | None = None,
    is_published: bool = True,
) -> ProgramHotel:
    if check_in_date >= check_out_date:
        raise ProgramHotelCreationError("Дата выезда должна быть позже даты заезда")

    if slots_total <= 0:
        raise ProgramHotelCreationError("Общее количество слотов должно быть положительным")

    if slots_available is None:
        slots_available = slots_total
    elif slots_available < 0:
        raise ProgramHotelCreationError("Доступное количество слотов не может быть отрицательным")

    if slots_available > slots_total:
        raise ProgramHotelCreationError(
            "Доступное количество слотов не может превышать общее количество слотов"
        )

    program_hotel = ProgramHotel(
        hotel_id=hotel_id,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        slots_total=slots_total,
        slots_available=slots_available,
        is_published=is_published,
    )
    db.add(program_hotel)
    db.commit()
    db.refresh(program_hotel)
    return program_hotel

#Хардкодим)
HIGH_USER_RATING_THRESHOLD = 7.0
MEDIUM_USER_RATING_THRESHOLD = 4.0

MEDIUM_HOTEL_RATING = 4
LOW_HOTEL_RATING = 3

"""Возвращает доступные отели программы по заданным критериям."""
def list_available_program_hotels(
    db: Session,
    *,
    home_city: str | None = None,
    preferred_city: str | None = None,
    guests_count: int = 1,
    user_rating: float = 0.0,
) -> Sequence[ProgramHotel]:
    
    if guests_count <= 0:
        raise ProgramHotelSelectionError(
            "Количество путешественников должно быть положительным"
        )

    normalized_rating = min(max(float(user_rating), 0.0), 10.0)

    query = (
        db.query(ProgramHotel)
        .join(ProgramHotel.hotel)
        .options(joinedload(ProgramHotel.hotel))
        .filter(
            ProgramHotel.is_published.is_(True),
            ProgramHotel.slots_available > 0,
        )
    )

    if guests_count > 1:
        query = query.filter(ProgramHotel.slots_available >= guests_count)

    #TODO: ближайшие города?
    cities = {city.strip() for city in (home_city, preferred_city) if city and city.strip()}
    if cities:
        query = query.filter(Hotel.city.in_(cities))

    if normalized_rating >= HIGH_USER_RATING_THRESHOLD:
        rating_filter = None
        ordering = Hotel.rating.desc()
    elif normalized_rating >= MEDIUM_USER_RATING_THRESHOLD:
        rating_filter = Hotel.rating <= MEDIUM_HOTEL_RATING
        ordering = Hotel.rating.desc()
    else:
        rating_filter = Hotel.rating <= LOW_HOTEL_RATING
        ordering = Hotel.rating.asc()

    if rating_filter is not None:
        query = query.filter(rating_filter)

    return query.order_by(ordering, ProgramHotel.created_at.desc()).all()