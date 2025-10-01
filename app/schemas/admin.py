from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.program_application import ProgramApplicationStatus
from app.schemas.report import ReportStatus


class SecretGuestApplicationRow(BaseModel):
    application_id: int
    user_id: int | None
    full_name: str
    email: str | None = None
    score: int = Field(ge=0)
    status: ProgramApplicationStatus
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecretGuestStatsRow(BaseModel):
    user_id: int
    full_name: str
    email: str | None = None
    level: int = Field(ge=0)
    reports_count: int = Field(ge=0)


class ReportModerationRow(BaseModel):
    report_id: str
    user_id: int | None
    full_name: str
    level: int | None = None
    hotel_id: int
    hotel_name: str
    status: ReportStatus
    overall_score: float | None = None
    submitted_at: datetime | None = None


class HotelCardReportPhoto(BaseModel):
    id: int
    url: str
    section: str


class HotelCardReportEntry(BaseModel):
    report_id: str
    score: float | None = None
    score_label: str
    submitted_at: datetime | None = None
    trip_type: str | None = None
    stay_context: str | None = None
    good_text: str | None = None
    bad_text: str | None = None
    advantages_text: str | None = None
    tags: list[str] = Field(default_factory=list)
    photos: list[HotelCardReportPhoto] = Field(default_factory=list)


class HotelCardReportList(BaseModel):
    hotel_id: int
    hotel_name: str | None = None
    total_reports: int
    average_score: float | None = None
    items: list[HotelCardReportEntry]
