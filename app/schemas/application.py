from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.program_application import ProgramApplicationStatus


class ApplicationBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    city: str | None = None
    motivation: str | None = None
    experience: str | None = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    id: int
    status: ProgramApplicationStatus
    reviewer_comment: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatusUpdate(BaseModel):
    status: ProgramApplicationStatus
    reviewer_comment: str | None = None


class ApplicationFilter(BaseModel):
    status: ProgramApplicationStatus | None = None
