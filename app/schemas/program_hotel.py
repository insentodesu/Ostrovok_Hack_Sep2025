from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from .hotel import HotelRead


class ProgramHotelBase(BaseModel):
    hotel_id: int
    check_in_date: datetime
    check_out_date: datetime


class ProgramHotelCreate(ProgramHotelBase):
    slots_total: int = 1

    @field_validator("slots_total")
    @classmethod
    def validate_slots_total(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Общее количество слотов должно быть положительным")
        return value

    @model_validator(mode="after")
    def validate_dates_and_slots(self) -> "ProgramHotelCreate":
        if self.check_in_date >= self.check_out_date:
            raise ValueError("Дата выезда должна быть позже даты заезда")
        return self


class ProgramHotelUpdate(BaseModel):
    hotel_id: int | None = None
    check_in_date: datetime | None = None
    check_out_date: datetime | None = None
    slots_total: int | None = None
    slots_available: int | None = None


class ProgramHotelRead(ProgramHotelBase):
    slots_total: int
    slots_available: int
    id: int
    created_at: datetime
    updated_at: datetime
    hotel: HotelRead | None = None

    model_config = ConfigDict(from_attributes=True)

class ProgramHotelAvailableDate(BaseModel):
    check_in_date: datetime
    check_out_date: datetime
    slots_available: int


class ProgramHotelAvailabilityRead(BaseModel):
    hotel: HotelRead
    available_dates: list[ProgramHotelAvailableDate]