from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_admin,
    get_current_active_user,
    get_db_session,
    get_optional_current_user,
)
from app.models.program_application import ProgramApplicationStatus
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatusUpdate,
)
from app.services import application_service

router = APIRouter()


@router.post(
    "/",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Подача заявки",
    description="Создаёт новую заявку на участие. Авторизованный пользователь может подать только одну заявку.",
)
def submit_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    if current_user and application_service.get_application_by_user(db, current_user.id):
        raise HTTPException(status_code=400, detail="Для пользователя уже существует заявка")

    existing_application = application_service.get_application_by_email(db, payload.email)
    if existing_application:
        raise HTTPException(status_code=400, detail="Заявка с таким email уже существует")

    user_id = current_user.id if current_user else None

    application = application_service.create_application(
        db,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        city=payload.city,
        motivation=payload.motivation,
        experience=payload.experience,
        user_id=user_id,
    )
    return application


@router.get(
    "/me",
    response_model=ApplicationRead,
    summary="Моя заявка",
    description="Возвращает заявку, связанную с текущим авторизованным пользователем.",
)
def get_my_application(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    application = application_service.get_application_by_user(db, current_user.id)
    if not application:
        raise HTTPException(status_code=404, detail="Для пользователя заявка не найдена")
    return application


@router.get(
    "/",
    response_model=list[ApplicationRead],
    summary="Список заявок",
    description="Доступно администраторам. Позволяет просмотреть заявки и отфильтровать их по статусу.",
)
def list_applications(
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
    status_filter: ProgramApplicationStatus | None = Query(
        None,
        alias="status",
        description="Фильтр по статусу заявки",
    ),
):
    applications = application_service.list_applications(db, status=status_filter)
    return applications


@router.get(
    "/{application_id}",
    response_model=ApplicationRead,
    summary="Просмотр заявки",
    description="Возвращает подробную информацию по конкретной заявке. Только для администраторов.",
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
):
    application = application_service.get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return application


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationRead,
    summary="Обновление статуса",
    description="Позволяет администратору изменить статус заявки и добавить комментарий.",
)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_admin),
):
    application = application_service.get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    updated_application = application_service.update_application_status(
        db,
        application=application,
        status=payload.status,
        reviewer_comment=payload.reviewer_comment,
    )
    return updated_application
