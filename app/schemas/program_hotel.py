from datetime import datetime
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:  # pragma: no cover - используется только для подсказок типов
    from .hotel import HotelRead


class ProgramHotelBase(BaseModel):
    hotel_id: int
    check_in_date: datetime
    check_out_date: datetime
    slots_total: int
    slots_available: int
    is_published: bool = True


class ProgramHotelCreate(ProgramHotelBase):
    pass


class ProgramHotelUpdate(BaseModel):
    hotel_id: int | None = None
    check_in_date: datetime | None = None
    check_out_date: datetime | None = None
    slots_total: int | None = None
    slots_available: int | None = None
    is_published: bool | None = None


class ProgramHotelRead(ProgramHotelBase):
    id: int
    created_at: datetime
    updated_at: datetime
    hotel: "HotelRead | None" = None

    model_config = ConfigDict(from_attributes=True)