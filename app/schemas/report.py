from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportBase(BaseModel):
    summary: str | None = None


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    summary: str | None = None


class ReportRead(ReportBase):
    id: int
    submitted_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)