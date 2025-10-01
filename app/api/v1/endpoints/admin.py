from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db_session
from app.models.user import User
from app.schemas.admin import (
    ReportModerationRow,
    SecretGuestApplicationRow,
    SecretGuestStatsRow,
)
from app.services import admin_service

router = APIRouter()


@router.get(
    "/secret-guests/applications",
    response_model=list[SecretGuestApplicationRow],
    summary="Активные заявки секретных гостей",
    description="Возвращает список одобренных кандидатов с их баллами",
)
def list_secret_guest_applications(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[SecretGuestApplicationRow]:
    return admin_service.list_secret_guest_applications(db)


@router.get(
    "/secret-guests/stats",
    response_model=list[SecretGuestStatsRow],
    summary="Статистика активных секретных гостей",
    description="Уровни и количество отчетов по активным секретным гостям",
)
def list_secret_guest_stats(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[SecretGuestStatsRow]:
    return admin_service.list_secret_guest_stats(db)


@router.get(
    "/reports/moderation",
    response_model=list[ReportModerationRow],
    summary="Очередь модерации отчетов",
)
def list_reports_on_moderation(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db_session),
) -> list[ReportModerationRow]:
    return admin_service.list_reports_on_moderation(db)
