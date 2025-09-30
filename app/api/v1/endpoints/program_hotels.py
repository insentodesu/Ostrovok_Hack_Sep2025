from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.models.user import User
from app.schemas.program_hotel import ProgramHotelCreate, ProgramHotelRead
from app.services import hotel_service, program_hotel_service
from app.services.program_hotel_service import ProgramHotelCreationError

router = APIRouter()


@router.post(
    "/",
    response_model=ProgramHotelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавление отеля в программу",
    description="Позволяет администратору вручную добавить отель в программу проверки.",
)
def create_program_hotel(
    payload: ProgramHotelCreate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
):
    hotel = hotel_service.get_hotel(db, payload.hotel_id)
    if hotel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отель не найден")

    try:
        program_hotel = program_hotel_service.create_program_hotel(
            db,
            hotel_id=payload.hotel_id,
            check_in_date=payload.check_in_date,
            check_out_date=payload.check_out_date,
            slots_total=payload.slots_total,
            slots_available=payload.slots_available,
            is_published=payload.is_published,
        )
    except ProgramHotelCreationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return program_hotel