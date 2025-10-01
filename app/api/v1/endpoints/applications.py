from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
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
    summary="Создание черновика анкеты",
    description="Создаёт новую анкету на участие. Авторизованный пользователь может подать только одну заявку.",
)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    if current_user and application_service.get_application_by_user(db, current_user.id):
        raise HTTPException(status_code=400, detail="Для пользователя уже существует заявка")

    user_id = current_user.id if current_user else None

    application = application_service.create_application(
        db,
        city_home=payload.city_home,
        city_desired=payload.city_desired,
        travel_party=payload.travel_party,
        answers=payload.answers.model_dump(),
        review_text=payload.review_text,
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

@router.post(
    "/{application_id}/photo",
    response_model=ApplicationRead,
    summary="Загрузка фотографии",
    description="Прикрепляет фотографию к анкете в статусе черновика.",
)
async def upload_application_photo(
    application_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    application = application_service.get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    if current_user and application.user_id and application.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения заявки")

    if application.status != ProgramApplicationStatus.draft:
        raise HTTPException(status_code=400, detail="Фотографии можно добавлять только к черновику")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Пустой файл нельзя загрузить")

    photo_path = application_service.store_application_photo(
        application_id=application.id,
        filename=file.filename,
        content=content,
    )

    updated_application = application_service.add_application_photo(
        db,
        application=application,
        photo_path=photo_path,
    )
    return updated_application


@router.post(
    "/{application_id}/submit",
    response_model=ApplicationRead,
    summary="Отправка анкеты на проверку",
    description="Переводит анкету из статуса черновика в модерацию.",
)
def submit_application_for_review(
    application_id: int,
    db: Session = Depends(get_db_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    application = application_service.get_application_by_id(db, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    if current_user and application.user_id and application.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для изменения заявки")

    if application.status != ProgramApplicationStatus.draft:
        raise HTTPException(status_code=400, detail="Анкета уже отправлена на проверку")

    if not application.photos:
        raise HTTPException(status_code=400, detail="Для отправки анкеты добавьте хотя бы одну фотографию")

    updated_application = application_service.submit_application(db, application=application)
    return updated_application