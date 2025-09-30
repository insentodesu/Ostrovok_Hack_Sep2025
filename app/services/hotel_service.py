from collections.abc import Sequence
from sqlalchemy.orm import Session
from app.models.hotel import Hotel


def create_hotel(
    db: Session,
    *,
    name: str,
    city: str,
    address: str,
    guests: int,
    cost: int,
    rating: int = 0,
) -> Hotel:
    if rating < 0 or rating > 5:
        raise ValueError("Рейтинг отеля должен быть в диапазоне от 0 до 5")
    hotel = Hotel(
        name=name,
        city=city,
        address=address,
        guests=guests,
        cost=cost,
        rating=rating,
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
    guests: int | None = None,
    cost: int | None = None,
    rating: int | None = None,
) -> Hotel:
    if name is not None:
        hotel.name = name
    if city is not None:
        hotel.city = city
    if address is not None:
        hotel.address = address
    if guests is not None:
        hotel.guests = guests
    if cost is not None:
        hotel.cost = cost
    if rating is not None:
        if rating < 0 or rating > 5:
            raise ValueError("Рейтинг отеля должен быть в диапазоне от 0 до 5")
        hotel.rating = rating
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel