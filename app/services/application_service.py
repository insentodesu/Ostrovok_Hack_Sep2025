from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models.program_application import ProgramApplication, ProgramApplicationStatus


def create_application(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    city: str | None = None,
    motivation: str | None = None,
    experience: str | None = None,
    user_id: int | None = None,
) -> ProgramApplication:
    application = ProgramApplication(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        city=city,
        motivation=motivation,
        experience=experience,
        user_id=user_id,
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


def get_application_by_email(db: Session, email: str) -> ProgramApplication | None:
    return db.query(ProgramApplication).filter(ProgramApplication.email == email).first()


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
