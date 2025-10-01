import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.report import PHOTO_SECTIONS, Photo, Report
from app.schemas.report import (
    PhotoSection,
    ReportRead,
    ReportStatus,
    ReportStep1Payload,
    ReportStep2Payload,
    ReportStep6Payload,
)


@dataclass(slots=True)
class IncomingPhoto:
    filename: str
    content: bytes
    content_type: str | None

    @property
    def size(self) -> int:
        return len(self.content)


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_report(
    db: Session,
    *,
    hotel_id: int,
    checkout_date: datetime,
    user_id: int | None,
) -> Report:
    report = Report(
        hotel_id=hotel_id,
        checkout_date=_to_utc(checkout_date),
        user_id=user_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: str) -> Report | None:
    return db.get(Report, report_id)


def editing_enabled(report: Report) -> bool:
    if report.status != ReportStatus.DRAFT.value:
        return False
    open_at = _to_utc(report.checkout_date) - timedelta(days=1)
    return _now_utc() >= open_at


def ensure_report_editable(report: Report) -> None:
    if report.status != ReportStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Отчет уже отправлен и недоступен для редактирования",
        )
    if not editing_enabled(report):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Форма будет доступна за день до выезда",
        )


def save_step(db: Session, report: Report, step: str, payload: dict[str, Any]) -> Report:
    answers = dict(report.answers or {})
    answers[step] = payload
    report.answers = answers
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def serialize_report(report: Report) -> ReportRead:
    return ReportRead.model_validate(
        {
            "id": report.id,
            "user_id": report.user_id,
            "hotel_id": report.hotel_id,
            "checkout_date": _to_utc(report.checkout_date),
            "status": report.status,
            "answers": report.answers or {},
            "overall_score": report.overall_score,
            "created_at": report.created_at,
            "updated_at": report.updated_at,
            "submitted_at": report.submitted_at,
            "editing_enabled": editing_enabled(report),
        }
    )


def serialize_photo(photo: Photo) -> dict[str, Any]:
    relative_path = Path(photo.path).as_posix()
    return {
        "id": photo.id,
        "report_id": photo.report_id,
        "section": photo.section,
        "filename": photo.filename,
        "path": relative_path,
        "mime": photo.mime,
        "size": photo.size,
        "created_at": photo.created_at,
        "url": f"{settings.static_url.rstrip('/')}/{relative_path}",
    }


def add_photos(
    db: Session,
    *,
    report: Report,
    section: PhotoSection,
    files: Iterable[IncomingPhoto],
) -> list[Photo]:
    storage_root = Path(settings.static_root)
    base_dir = storage_root / settings.report_photos_prefix / report.id / section.value
    base_dir.mkdir(parents=True, exist_ok=True)

    stored: list[Photo] = []
    for incoming in files:
        if not incoming.filename:
            continue
        suffix = Path(incoming.filename).suffix
        unique_name = f"{uuid.uuid4().hex}{suffix}" if suffix else uuid.uuid4().hex
        relative_path = Path(settings.report_photos_prefix) / report.id / section.value / unique_name
        file_path = storage_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(incoming.content)

        photo = Photo(
            report_id=report.id,
            section=section.value,
            filename=incoming.filename,
            path=relative_path.as_posix(),
            mime=incoming.content_type,
            size=incoming.size,
        )
        db.add(photo)
        stored.append(photo)

    if not stored:
        return []

    db.commit()
    for photo in stored:
        db.refresh(photo)
    return stored


def list_photos(db: Session, *, report: Report, section: PhotoSection | None = None) -> list[Photo]:
    stmt = select(Photo).where(Photo.report_id == report.id)
    if section is not None:
        stmt = stmt.where(Photo.section == section.value)
    stmt = stmt.order_by(Photo.id.asc())
    return list(db.scalars(stmt))


def _validated_step(step_data: dict[str, Any] | None, model: type[ReportStep1Payload], step_name: str):
    if not step_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": f"Данные шага {step_name} отсутствуют"},
        )
    try:
        return model.model_validate(step_data)
    except ValidationError as exc:  # pragma: no cover - pydantic formatting
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": f"Ошибки валидации шага {step_name}", "errors": exc.errors()},
        ) from exc


def submit_report(db: Session, report: Report) -> Report:
    ensure_report_editable(report)

    step1 = _validated_step(report.answers.get("step1"), ReportStep1Payload, "1")
    step2 = _validated_step(report.answers.get("step2"), ReportStep2Payload, "2")
    step6 = _validated_step(report.answers.get("step6"), ReportStep6Payload, "6")

    required_photo_counts = {"photos_match": 5, "cleanliness": 5}
    section_counts: dict[str, int] = {}
    for section_name in PHOTO_SECTIONS:
        count = db.scalar(
            select(func.count()).where(Photo.report_id == report.id, Photo.section == section_name)
        )
        section_counts[section_name] = int(count or 0)

    missing_sections = {
        section: {
            "required": required_photo_counts[section],
            "actual": section_counts.get(section, 0),
        }
        for section in required_photo_counts
        if section_counts.get(section, 0) < required_photo_counts[section]
    }
    if missing_sections:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Недостаточно фотографий",
                "sections": missing_sections,
            },
        )

    scores = [
        step1.room_cleanliness,
        step1.bathroom_sanitation,
        step1.linen_freshness,
        step1.public_area_cleanliness,
        step2.politeness,
        step2.response_speed,
        step2.food_quality,
    ]
    overall = round(sum(scores) / len(scores), 1)

    answers = dict(report.answers or {})
    answers["step1"] = step1.model_dump()
    answers["step2"] = step2.model_dump()
    answers["step6"] = step6.model_dump()

    report.answers = answers
    report.overall_score = overall
    report.status = ReportStatus.ON_MODERATION.value
    report.submitted_at = _now_utc()

    db.add(report)
    db.commit()
    db.refresh(report)
    return report