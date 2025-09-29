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
) -> User:
    hashed_password = get_password_hash(password)

    user = User(
        email=email,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        role=role,
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
