from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.models.user import User
from app.schemas.hotel import HotelCreate, HotelRead, HotelUpdate
from app.services import hotel_service

router = APIRouter()


@router.post(
    "/",
    response_model=HotelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание отеля",
    description="Создает новый отель. Доступно только админам.",
)
def create_hotel(
    payload: HotelCreate,
    db: Session = Depends(get_db_session),
    #_: User = Depends(get_current_admin),
):
    hotel = hotel_service.create_hotel(
        db,
        name=payload.name,
        city=payload.city,
        address=payload.address,
        rooms_total=payload.rooms_total,
        description=payload.description,
        is_active=payload.is_active,
    )
    return hotel


@router.get(
    "/",
    response_model=list[HotelRead],
    summary="Список отелей",
    description="Возвращает список отелей. Можно отфильтровать по признаку активности.",
)
def list_hotels(
    db: Session = Depends(get_db_session),
    is_active: bool | None = Query(
        default=None,
        description="Фильтр по активности отеля",
    ),
):
    return hotel_service.list_hotels(db, is_active=is_active)


@router.get(
    "/{hotel_id}",
    response_model=HotelRead,
    summary="Информация об отеле",
    description="Возвращает информацию об отеле по идентификатору.",
)
def get_hotel(hotel_id: int, db: Session = Depends(get_db_session)):
    hotel = hotel_service.get_hotel(db, hotel_id)
    if hotel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отель не найден")
    return hotel


@router.patch(
    "/{hotel_id}",
    response_model=HotelRead,
    summary="Обновление отеля",
    description="Обновляет информацию об отеле. Доступно только администраторам.",
)
def update_hotel(
    hotel_id: int,
    payload: HotelUpdate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
):
    hotel = hotel_service.get_hotel(db, hotel_id)
    if hotel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отель не найден")

    update_data = payload.model_dump(exclude_unset=True)
    updated_hotel = hotel_service.update_hotel(db, hotel=hotel, **update_data)
    return updated_hotel