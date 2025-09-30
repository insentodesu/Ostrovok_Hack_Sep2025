from datetime import datetime
from collections import OrderedDict
from collections.abc import Sequence

from sqlalchemy.orm import Session, joinedload

from app.models.hotel import Hotel
from app.models.program_hotel import ProgramHotel
from app.models.user import User


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

HIGH_USER_RATING_THRESHOLD = 7.0
MEDIUM_USER_RATING_THRESHOLD = 4.0

MEDIUM_HOTEL_RATING = 4
LOW_HOTEL_RATING = 3

def _normalize_user_rating(user_rating: float) -> float:
    return min(max(float(user_rating), 0.0), 10.0)


def _build_available_hotels_query(
    db: Session,
    *,
    cities: list[str],
    guests_count: int,
    normalized_rating: float,
    with_joinedload: bool,
):
    query = (
        db.query(ProgramHotel)
        .join(ProgramHotel.hotel)
        .filter(
            ProgramHotel.slots_available > 0,
        )
    )

    if with_joinedload:
        query = query.options(joinedload(ProgramHotel.hotel))

    if cities:
        query = query.filter(Hotel.city.in_(cities), Hotel.guests >= guests_count)

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

    return query, ordering

"""Возвращает доступные отели программы по заданным критериям."""
def list_available_program_hotels(
    db: Session,
    *,
    user: User
) -> Sequence[ProgramHotel]:

    normalized_rating = _normalize_user_rating(user.rating)
    query, ordering = _build_available_hotels_query(
        db,
        cities=user.cities,
        normalized_rating=normalized_rating,
        with_joinedload=True,
    )

    return query.order_by(ordering, ProgramHotel.created_at.desc()).all()

def list_available_program_hotels_with_dates(
    db: Session,
    *,
    user: User,
    limit: int | None = None,
) -> list[dict]:
    """Группирует доступные отели программы по самим отелям и датам."""

    program_hotels = list_available_program_hotels(
        db,
        user=user,
    )

    grouped_hotels: OrderedDict[int, dict] = OrderedDict()

    for program_hotel in program_hotels:
        hotel = program_hotel.hotel
        if hotel is None:
            continue

        hotel_entry = grouped_hotels.get(program_hotel.hotel_id)

        if hotel_entry is None:
            if limit is not None and len(grouped_hotels) >= limit:
                continue

            hotel_entry = {
                "hotel": hotel,
                "available_dates": [],
            }
            grouped_hotels[program_hotel.hotel_id] = hotel_entry

        hotel_entry["available_dates"].append(
            {
                "check_in_date": program_hotel.check_in_date,
                "check_out_date": program_hotel.check_out_date,
                "slots_available": program_hotel.slots_available,
            }
        )

    return list(grouped_hotels.values())

def is_hotel_available_for_user(
    db: Session,
    *,
    hotel_id: int,
    user: User,
) -> bool:

    normalized_rating = _normalize_user_rating(user.rating)
    query, _ = _build_available_hotels_query(
        db,
        cities=user.cities,
        guests_count=user.guests,
        normalized_rating=normalized_rating,
        with_joinedload=False,
    )

    return (
        query.filter(ProgramHotel.hotel_id == hotel_id)
        .order_by(ProgramHotel.created_at.desc())
        .first()
        is not None
    )