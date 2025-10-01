from pydantic import BaseModel, ConfigDict, EmailStr, Field

from datetime import date

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
    model_config = ConfigDict(from_attributes=True)
