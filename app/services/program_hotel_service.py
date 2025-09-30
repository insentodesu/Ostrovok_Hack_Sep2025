from datetime import datetime

from sqlalchemy.orm import Session

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