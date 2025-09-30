from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class PromocodeBase(BaseModel):
    code: str
    valid_until: date


class PromocodeCreate(PromocodeBase):
    pass


class PromocodeUpdate(BaseModel):
    code: str | None = None
    valid_until: date | None = None


class PromocodeRead(PromocodeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)