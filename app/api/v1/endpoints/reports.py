from typing import Sequence

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.report import (
    PhotoSection,
    ReportCreate,
    ReportPhotoRead,
    ReportRead,
    ReportStep1Payload,
    ReportStep2Payload,
    ReportStep6Payload,
)
from app.services import report_service

router = APIRouter()


def _get_report_or_404(db: Session, report_id: str):
    report = report_service.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отчет не найден")
    return report


def _parse_section(section: str) -> PhotoSection:
    try:
        return PhotoSection(section)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Неизвестная секция фото") from exc


@router.post(
    "/",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создание отчета",
    description="Создает черновик отчета о пребывании",
)
def create_report(payload: ReportCreate, db: Session = Depends(get_db_session)) -> ReportRead:
    report = report_service.create_report(
        db,
        hotel_name=payload.hotel_name,
        checkout_date=payload.checkout_date,
        user_id=payload.user_id,
    )
    return report_service.serialize_report(report)


@router.get(
    "/{report_id}",
    response_model=ReportRead,
    summary="Получение отчета",
    description="Возвращает данные отчета о пребывании",
)
def get_report(report_id: str, db: Session = Depends(get_db_session)) -> ReportRead:
    report = _get_report_or_404(db, report_id)
    return report_service.serialize_report(report)


@router.patch(
    "/{report_id}/step1",
    response_model=ReportRead,
    summary="Сохранение шага 1",
)
def save_step1(
    report_id: str,
    payload: ReportStep1Payload,
    db: Session = Depends(get_db_session),
) -> ReportRead:
    report = _get_report_or_404(db, report_id)
    report_service.ensure_report_editable(report)
    updated = report_service.save_step(db, report, "step1", payload.model_dump())
    return report_service.serialize_report(updated)


@router.patch(
    "/{report_id}/step2",
    response_model=ReportRead,
    summary="Сохранение шага 2",
)
def save_step2(
    report_id: str,
    payload: ReportStep2Payload,
    db: Session = Depends(get_db_session),
) -> ReportRead:
    report = _get_report_or_404(db, report_id)
    report_service.ensure_report_editable(report)
    updated = report_service.save_step(db, report, "step2", payload.model_dump())
    return report_service.serialize_report(updated)


@router.patch(
    "/{report_id}/step6",
    response_model=ReportRead,
    summary="Сохранение шага 6",
)
def save_step6(
    report_id: str,
    payload: ReportStep6Payload,
    db: Session = Depends(get_db_session),
) -> ReportRead:
    report = _get_report_or_404(db, report_id)
    report_service.ensure_report_editable(report)
    updated = report_service.save_step(db, report, "step6", payload.model_dump())
    return report_service.serialize_report(updated)


@router.post(
    "/{report_id}/photos/{section}",
    response_model=list[ReportPhotoRead],
    summary="Загрузка фотографий",
    description="Загружает фотографии для выбранной секции",
)
async def upload_photos(
    report_id: str,
    section: str,
    files: Sequence[UploadFile] = File(...),
    db: Session = Depends(get_db_session),
) -> list[ReportPhotoRead]:
    report = _get_report_or_404(db, report_id)
    report_service.ensure_report_editable(report)
    section_enum = _parse_section(section)

    incoming = []
    for file in files:
        content = await file.read()
        file.file.close()
        incoming.append(
            report_service.IncomingPhoto(
                filename=file.filename or "",
                content=content,
                content_type=file.content_type,
            )
        )

    saved = report_service.add_photos(db, report=report, section=section_enum, files=incoming)
    return [ReportPhotoRead.model_validate(report_service.serialize_photo(photo)) for photo in saved]


@router.get(
    "/{report_id}/photos",
    response_model=list[ReportPhotoRead],
    summary="Список фотографий",
)
def list_photos(
    report_id: str,
    section: PhotoSection | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> list[ReportPhotoRead]:
    report = _get_report_or_404(db, report_id)
    photos = report_service.list_photos(db, report=report, section=section)
    return [ReportPhotoRead.model_validate(report_service.serialize_photo(photo)) for photo in photos]


@router.post(
    "/{report_id}/submit",
    response_model=ReportRead,
    summary="Отправка отчета",
)
def submit_report(report_id: str, db: Session = Depends(get_db_session)) -> ReportRead:
    report = _get_report_or_404(db, report_id)
    submitted = report_service.submit_report(db, report)
    return report_service.serialize_report(submitted)