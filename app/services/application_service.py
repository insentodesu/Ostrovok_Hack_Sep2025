from collections.abc import Sequence
import datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.program_application import ProgramApplication, ProgramApplicationStatus
from app.models.user import User

from app.services.upload_utils import IncomingUpload

RAW_SCORE_RULES: dict[str, dict[str, int]] = {
    "q4": {"a": -1, "b": 1, "c": 0},
    "q5": {"a": -1, "b": 1, "c": 0},
    "q6": {"a": 0, "b": 1, "c": -1},
    "q7": {"a": 0, "b": 1, "c": -1},
    "q8": {"a": 1, "b": -1, "c": 0},
}

RAW_SCORE_MIN = -4
RAW_SCORE_MAX = 5
NORMALIZED_SCORE_MAX = 12
MIN_PHOTOS = 2
MAX_PHOTOS = 4
MIN_REVIEW_LENGTH = 100
MAX_REVIEW_LENGTH = 2000

USER_BONUS_MAX = 7
TOTAL_SCORE_MAX = NORMALIZED_SCORE_MAX + USER_BONUS_MAX

ACTIVE_STATUSES = {
    ProgramApplicationStatus.draft,
    ProgramApplicationStatus.in_review,
}

ACTIVE_APPLICATION_TTL_DAYS = 90

_ACCEPTED_USER_ROLE = "accepted"


def _calculate_raw_score(answers: dict[str, str]) -> int:
    score = 0
    for question, mapping in RAW_SCORE_RULES.items():
        answer = answers.get(question)
        if answer is None:
            raise ValueError(f"Отсутствует ответ на вопрос {question}")
        if answer not in mapping:
            raise ValueError(f"Недопустимый ответ '{answer}' для вопроса {question}")
        score += mapping[answer]
    return score


def _calculate_user_bonus(user: User | None) -> int:
    if user is None:
        return 0

    bonus = 0

    created_at = getattr(user, "created_at", None)
    if isinstance(created_at, datetime.datetime):
        created_at_dt = created_at
        if created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=datetime.UTC)
        now = datetime.datetime.now(datetime.UTC)
        years_on_platform = now.year - created_at_dt.year - (
            (now.month, now.day) < (created_at_dt.month, created_at_dt.day)
        )
        if years_on_platform >= 3:
            bonus += 3
        elif years_on_platform >= 2:
            bonus += 2
        elif years_on_platform >= 1:
            bonus += 1

    guru_level = getattr(user, "guru_level", 0) or 0
    if isinstance(guru_level, int):
        bonus += max(0, min(guru_level, 4))

    return bonus


def normalize_score(raw_score: int) -> int:
    clamped = min(max(raw_score, RAW_SCORE_MIN), RAW_SCORE_MAX)
    normalized = round((clamped - RAW_SCORE_MIN) / (RAW_SCORE_MAX - RAW_SCORE_MIN) * NORMALIZED_SCORE_MAX)
    return max(0, min(normalized, NORMALIZED_SCORE_MAX))


def determine_status_by_score(score: int) -> ProgramApplicationStatus:
    if score <= 4:
        return ProgramApplicationStatus.rejected
    if score <= 8:
        return ProgramApplicationStatus.in_review
    return ProgramApplicationStatus.accepted


def calculate_application_score(application: ProgramApplication) -> int:
    raw_score = _calculate_raw_score(application.answers)
    user_bonus = _calculate_user_bonus(getattr(application, "user", None))
    return raw_score + user_bonus


def _promote_applicant(db: Session, application: ProgramApplication) -> None:
    if not application.user_id:
        return

    user: User | None = db.get(User, application.user_id)
    if user is None:
        return

    if user.role in ("admin", _ACCEPTED_USER_ROLE):
        return

    user.role = _ACCEPTED_USER_ROLE
    db.add(user)


def create_application(
    db: Session,
    *,
    city_home: str,
    city_desired: str,
    travel_party: str,
    answers: dict,
    review_text: str,
    user_id: int,
) -> ProgramApplication:
    application = ProgramApplication(
        city_home=city_home.strip(),
        city_desired=city_desired.strip(),
        travel_party=travel_party,
        answers=answers,
        review_text=review_text,
        photos=[],
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


def get_active_application_by_user(db: Session, user_id: int) -> ProgramApplication | None:
    freshness_threshold = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=ACTIVE_APPLICATION_TTL_DAYS)
    return (
        db.query(ProgramApplication)
        .filter(
            ProgramApplication.user_id == user_id,
            ProgramApplication.status == ACTIVE_STATUSES,
            ProgramApplication.created_at >= freshness_threshold,
        )
        .order_by(ProgramApplication.created_at.desc())
        .first()
    )


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
    existing_photos = list(application.photos or [])
    if len(existing_photos) + len(photo_paths) > MAX_PHOTOS:
        raise ValueError("Можно загрузить не более четырёх фотографий")
    existing_photos.extend(photo_paths)
    application.photos = existing_photos
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def submit_application(
    db: Session,
    *,
    application: ProgramApplication,
) -> ProgramApplication:
    total_score = calculate_application_score(application)
    target_status = determine_status_by_score(total_score)

    if total_score <= 4:
        reviewer_comment = (
            "На данном этапе мы ищем участников с большим вниманием к деталям в отзывах. "
            "Вы можете подать новую заявку через 3 месяца. А пока вы можете помочь другим "
            "путешественникам, оставляя обычные отзывы после своих поездок!"
        )
    elif total_score <= 8:
        reviewer_comment = "Спасибо за обращение, рассмотрим вашу заявку в течении 3 дней!"
    else:
        reviewer_comment = (
            'Ваша кандидатура одобрена на участие в программе "Секретный гость"'
        )

    application.reviewer_comment = reviewer_comment
    application.status = target_status
    application.score = total_score

    if target_status == ProgramApplicationStatus.accepted:
        _promote_applicant(db, application)

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


def is_user_eligible(user: User, db: Session) -> tuple[bool, str | None]:
    active_application = get_active_application_by_user(db, user.id)
    if active_application:
        return False, "дождаться завершения текущей заявки/участия"

    if not user.email_verified or not user.phone_verified:
        return False, "подтвердить телефон и e-mail"

    if user.completed_bookings_last_year < 4:
        return False, "иметь не менее 4 завершённых бронирований с отзывами за 12 месяцев"

    if not user.date_of_birth:
        return False, "достичь 21 года"

    today = datetime.date.today()
    age = today.year - user.date_of_birth.year - (
        (today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day)
    )
    if age < 21:
        return False, "достичь 21 года"

    return True, None
