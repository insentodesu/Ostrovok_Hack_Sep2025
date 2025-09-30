from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from app.models.inspection import InspectionStatus

from .hotel import HotelRead
from .report import ReportRead
from .user import UserRead


class InspectionSelectRequest(BaseModel):
    hotel_id: int

class InspectionBase(BaseModel):
    hotel_id: int
    guest_id: int
    report_id: int | None = None
    status: InspectionStatus = InspectionStatus.awaiting_booking

 
class InspectionCreate(InspectionBase):
    pass


class InspectionUpdate(BaseModel):
    hotel_id: int | None = None
    guest_id: int | None = None
    report_id: int | None = None
    status: InspectionStatus | None = None


class InspectionRead(InspectionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    hotel: HotelRead | None = None
    guest: UserRead | None = None
    report: ReportRead | None = None

    model_config = ConfigDict(from_attributes=True)