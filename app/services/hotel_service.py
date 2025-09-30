from collections.abc import Sequence
from sqlalchemy.orm import Session
from app.models.hotel import Hotel


def create_hotel(
    db: Session,
    *,
    name: str,
    city: str,
    address: str,
    rooms_total: int | None = None,
    description: str | None = None,
    is_active: bool = True,
) -> Hotel:
    hotel = Hotel(
        name=name,
        city=city,
        address=address,
        rooms_total=rooms_total,
        description=description,
        is_active=is_active,
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel


def list_hotels(
    db: Session,
    *,
    is_active: bool | None = None,
) -> Sequence[Hotel]:
    query = db.query(Hotel).order_by(Hotel.created_at.desc())
    if is_active is not None:
        query = query.filter(Hotel.is_active == is_active)
    return query.all()


def get_hotel(db: Session, hotel_id: int) -> Hotel | None:
    return db.get(Hotel, hotel_id)


def update_hotel(
    db: Session,
    *,
    hotel: Hotel,
    name: str | None = None,
    city: str | None = None,
    address: str | None = None,
    rooms_total: int | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> Hotel:
    if name is not None:
        hotel.name = name
    if city is not None:
        hotel.city = city
    if address is not None:
        hotel.address = address
    if rooms_total is not None:
        hotel.rooms_total = rooms_total
    if description is not None:
        hotel.description = description
    if is_active is not None:
        hotel.is_active = is_active

    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel