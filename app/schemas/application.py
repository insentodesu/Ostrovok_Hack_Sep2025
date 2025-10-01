from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.models.program_application import ProgramApplicationStatus


class ApplicationAnswers(BaseModel):
    q4: Literal["a", "b", "c"]
    q5: Literal["a", "b", "c"]
    q6: Literal["a", "b", "c"]
    q7: Literal["a", "b", "c"]
    q8: Literal["a", "b", "c"]

class ApplicationBase(BaseModel):
    city_home: str = Field(..., description="Город проживания")
    city_desired: str = Field(..., description="Желаемый город пребывания")
    travel_party: Literal["a", "b", "c"] = Field(
        ..., description="С кем путешествует кандидат"
    )
    answers: ApplicationAnswers
    review_text: str = Field(..., description="Текст отзыва секретного гостя")


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    id: int
    status: ProgramApplicationStatus
    reviewer_comment: str | None
    photos: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatusUpdate(BaseModel):
    status: ProgramApplicationStatus
    reviewer_comment: str | None = None


class ApplicationFilter(BaseModel):
    status: ProgramApplicationStatus | None = None

class EligibilityResponse(BaseModel):
    eligible: bool
    reason: str | None = None