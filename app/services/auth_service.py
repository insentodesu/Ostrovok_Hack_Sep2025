from sqlalchemy import Date
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "candidate",
    cities: list[str] | None = None,
    guests: int | None = None,
    date_of_birth: Date | None = None,
    email_verified: bool | None = None,
    phone_verified: bool | None = None,
    completed_bookings_last_year: int | None = None,
    guru_level: int | None = None,
) -> User:
    hashed_password = get_password_hash(password)

    user = User(
        email=email,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth if date_of_birth is not None else None,
        email_verified=email_verified if email_verified is not None else False,
        phone_verified=phone_verified if phone_verified is not None else False,
        completed_bookings_last_year=completed_bookings_last_year if completed_bookings_last_year is not None else 0,
        role=role,
        guru_level=guru_level if guru_level is not None else 0,
        cities=list(cities) if cities is not None else [],
        guests=guests if guests is not None else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user:
        return None

    is_valid = verify_password(password, user.hashed_password)
    if not is_valid:
        return None
    return user
