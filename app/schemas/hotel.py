from datetime import datetime
from pydantic import BaseModel, ConfigDict


class HotelBase(BaseModel):
    name: str
    city: str
    address: str
    rooms_total: int | None = None
    description: str | None = None
    is_active: bool = True


class HotelCreate(HotelBase):
    pass


class HotelUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    rooms_total: int | None = None
    description: str | None = None
    is_active: bool | None = None


class HotelRead(HotelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)