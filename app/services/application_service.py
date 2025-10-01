from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.program_application import ProgramApplication, ProgramApplicationStatus

from app.services.upload_utils import IncomingUpload

def create_application(
    db: Session,
    *,
    city_home: str,
    city_desired: str,
    travel_party: str,
    answers: dict,
    review_text: str,
    user_id: int | None = None,
) -> ProgramApplication:
    application = ProgramApplication(
        city_home=city_home,
        city_desired=city_desired,
        travel_party=travel_party,
        answers=answers,
        review_text=review_text,
        photos=[],
        user_id = user_id,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_applications(
    db: Session,
    *,
    status: ProgramApplicationStatus | None = None,
) -> Sequence[ProgramApplication]:
    query = db.query(ProgramApplication).order_by(ProgramApplication.created_at.desc())
    if status is not None:
        query = query.filter(ProgramApplication.status == status)
    return query.all()


def get_application_by_id(db: Session, application_id: int) -> ProgramApplication | None:
    return db.query(ProgramApplication).filter(ProgramApplication.id == application_id).first()


def get_application_by_user(db: Session, user_id: int) -> ProgramApplication | None:
    return db.query(ProgramApplication).filter(ProgramApplication.user_id == user_id).first()


def update_application_status(
    db: Session,
    *,
    application: ProgramApplication,
    status: ProgramApplicationStatus,
    reviewer_comment: str | None = None,
) -> ProgramApplication:
    application.status = status
    application.reviewer_comment = reviewer_comment
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

def add_application_photos(
    db: Session,
    *,
    application: ProgramApplication,
    photo_paths: Sequence[str],
) -> ProgramApplication:
    if not photo_paths:
        return application
    photos = list(application.photos or [])
    photos.extend(photo_paths)
    application.photos = photos
    db.add(application)
    db.commit()
    db.refresh(application)
    return application

def submit_application(
    db: Session,
    *,
    application: ProgramApplication,
) -> ProgramApplication:
    application.status = ProgramApplicationStatus.in_review
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def store_application_photos(
    *,
    application_id: int,
    files: Sequence[IncomingUpload],
) -> list[str]:
    storage_dir = Path(settings.static_root)
    media_prefix = Path(settings.application_photos_prefix)

    (storage_dir / media_prefix).mkdir(parents=True, exist_ok=True)

    stored_paths: list[str] = []
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    for upload in files:
        original_extension = Path(upload.filename or "").suffix.lower()
        extension = original_extension if original_extension in allowed_extensions else ".jpg"

    file_name = f"{application_id}_{uuid4().hex}{extension}"
    file_path = storage_dir / media_prefix / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(upload.content)
    stored_paths.append(str(file_path))

    return stored_paths