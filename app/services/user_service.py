from sqlalchemy.orm import Session

from app.models.user import User


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def update_user_profile(
    db: Session,
    *,
    user: User,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
