from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class HotelBase(BaseModel):
    name: str
    city: str
    address: str
    cost: int = Field(default=1, ge=1)
    guests: int = Field(default=1, ge=1)
    rating: int = Field(default=0, ge=0, le=5)


class HotelCreate(HotelBase):
    pass


class HotelUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    cost: int | None = Field(default=None, ge=1)
    guests: int | None = Field(default=None, ge=1)
    description: str | None = None
    rating: int | None = Field(default=None, ge=0, le=5)


class HotelRead(HotelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)