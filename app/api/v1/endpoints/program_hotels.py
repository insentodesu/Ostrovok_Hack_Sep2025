from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user, get_db_session
from app.models.user import User
from app.schemas.program_hotel import (
    ProgramHotelAvailabilityRead,
    ProgramHotelAvailableDate,
    ProgramHotelCreate,
    ProgramHotelRead,
    ProgramHotelUpdate,
)
from app.services import hotel_service, program_hotel_service
from app.services.program_hotel_service import (
    ProgramHotelCreationError,
    ProgramHotelSelectionError,
    ProgramHotelUpdateError,
)

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
    #_: User = Depends(get_current_admin),
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
            is_published=payload.is_published,
        )
    except ProgramHotelCreationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return program_hotel

@router.get(
    "/",
    response_model=list[ProgramHotelRead],
    summary="Список отелей программы",
    description="Возвращает список всех отелей программы. Доступно только администраторам.",
)
def list_program_hotels(
    is_published: bool | None = Query(
        default=None,
        description="Фильтр по публикации отеля программы",
    ),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
):
    return program_hotel_service.list_program_hotels(db, is_published=is_published)

@router.get(
    "/available",
    response_model=list[ProgramHotelAvailabilityRead],
    summary="Доступные отели программы",
    description=(
        "Возвращает список отелей, которые доступны для проверки гостем"
    ),
)
def list_available_program_hotels_for_user(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    MAX_HOTELS_RETURNED = 5

    user_id = user.id
    del user_id  # TODO: использовать при расчёте пользовательского рейтинга

    try:
        program_hotels = program_hotel_service.list_available_program_hotels_with_dates(
            db,
            user=user,
            limit=MAX_HOTELS_RETURNED,
        )
    except ProgramHotelSelectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return [
        ProgramHotelAvailabilityRead(
            hotel=hotel_info["hotel"],
            available_dates=[
                ProgramHotelAvailableDate(**date_info)
                for date_info in hotel_info["available_dates"]
            ],  
        )
        for hotel_info in program_hotels
    ]

@router.patch(
    "/{program_hotel_id}",
    response_model=ProgramHotelRead,
    summary="Обновление отеля программы",
    description="Позволяет администратору обновить параметры отеля программы.",
)
def update_program_hotel(
    program_hotel_id: int,
    payload: ProgramHotelUpdate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
):
    program_hotel = program_hotel_service.get_program_hotel(db, program_hotel_id)
    if program_hotel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отель программы не найден")

    update_data = payload.model_dump(exclude_unset=True)

    try:
        updated_program_hotel = program_hotel_service.update_program_hotel(
            db,
            program_hotel=program_hotel,
            **update_data,
        )
    except ProgramHotelUpdateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return updated_program_hotel