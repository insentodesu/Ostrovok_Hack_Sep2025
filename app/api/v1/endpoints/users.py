from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db_session
from app.models.user import User
from app.schemas.user import (
    UserDashboard,
    UserDashboardRecommendation,
    UserRead,
    UserUpdate,
)
from app.services import user_service

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    summary="Получение профиля",
    description="Возвращает данные профиля авторизованного пользователя.",
)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Обновление профиля",
    description="Позволяет изменить имя и фамилию текущего пользователя.",
)
def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    updated_user = user_service.update_user_profile(
        db,
        user=current_user,
        first_name=payload.first_name,
        last_name=payload.last_name,
        cities=payload.cities,
        guests=payload.guests,
    )
    return updated_user


@router.get(
    "/me/dashboard",
    response_model=UserDashboard,
    summary="Личный кабинет секретного гостя",
    description="Возвращает промокод, статус участия и рекомендации по проверкам.",
)
def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> UserDashboard:
    return user_service.get_user_dashboard(db, user=current_user)


@router.get(
    "/me/recommendations",
    response_model=list[UserDashboardRecommendation],
    summary="Подбор отелей для проверки",
)
def get_recommendations(
    limit: int = Query(5, ge=1, le=20, description="Максимальное количество рекомендаций"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> list[UserDashboardRecommendation]:
    return user_service.get_user_recommendations(db, user=current_user, limit=limit)
