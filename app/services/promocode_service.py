import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.promocode import Promocode

_PROMOCODE_ALPHABET = string.ascii_uppercase + string.digits


def generate_promocode(*, length: int = 12, prefix: str | None = None) -> str:
    if length <= 0:
        raise ValueError("Длина промокода должна быть больше нуля.")

    prefix_value = prefix or ""
    remaining_length = length - len(prefix_value)
    if remaining_length <= 0:
        raise ValueError("Длина промокода должна быть больше длины префикса.")

    random_part = "".join(secrets.choice(_PROMOCODE_ALPHABET) for _ in range(remaining_length))
    return f"{prefix_value}{random_part}"


def generate_unique_promocode(
    db: Session,
    *,
    length: int = 12,
    prefix: str | None = None,
    max_attempts: int = 20,
) -> str:
    """Генерация уникального промокода, которого нет в базе"""

    for _ in range(max_attempts):
        candidate = generate_promocode(length=length, prefix=prefix)
        exists = db.execute(select(Promocode.id).where(Promocode.code == candidate)).first()
        if not exists:
            return candidate
    raise RuntimeError("Не возможно сгенерировать уникальный промокод")