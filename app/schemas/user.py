from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.report import ReportStatus


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str
    cities: list[str] | None = None
    guests: int | None = None
    date_of_birth: date | None = None
    email_verified: bool | None = None
    phone_verified: bool | None = None
    completed_bookings_last_year: int | None = None
    guru_level: int | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    cities: list[str] | None = None
    guests: int | None = None
    date_of_birth: date | None = None
    email_verified: bool | None = None
    phone_verified: bool | None = None
    completed_bookings_last_year: int | None = None
    guru_level: int | None = None


class UserRead(UserBase):
    id: int
    role: str
    cities: list[str] = Field(default_factory=list)
    guests: int | None = None
    rating: int = 0
    date_of_birth: date | None = None
    email_verified: bool = False
    phone_verified: bool = False
    completed_bookings_last_year: int = 0
    guru_level: int = 0
    model_config = ConfigDict(from_attributes=True)


class UserDashboardAssignedHotel(BaseModel):
    report_id: str
    hotel_id: int
    hotel_name: str
    status: ReportStatus
    checkout_date: datetime | None = None
    can_submit: bool


class UserDashboardRecommendationDate(BaseModel):
    check_in_date: datetime
    check_out_date: datetime
    slots_available: int


class UserDashboardRecommendation(BaseModel):
    hotel_id: int
    hotel_name: str
    city: str
    rating: int
    cost: int
    guests: int
    available_dates: list[UserDashboardRecommendationDate] = Field(default_factory=list)


class UserDashboard(BaseModel):
    promo_code: str
    participation_status: str
    can_submit_report: bool
    assigned_hotel: UserDashboardAssignedHotel | None = None
    recommendations: list[UserDashboardRecommendation] = Field(default_factory=list)
