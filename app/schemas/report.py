from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReportStatus(str, Enum):
    DRAFT = "draft"
    ON_MODERATION = "on_moderation"
    APPROVED = "approved"
    REJECTED = "rejected"


class PhotoSection(str, Enum):
    PHOTOS_MATCH = "photos_match"
    CLEANLINESS = "cleanliness"
    FOOD = "food"
    GENERAL = "general"


class ReportCreate(BaseModel):
    hotel_id: int = Field(gt=0)
    checkout_date: datetime
    user_id: int | None = Field(default=None, gt=0)


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int | None
    hotel_id: int
    checkout_date: datetime
    status: ReportStatus
    answers: dict[str, Any] = Field(default_factory=dict)
    overall_score: float | None = None
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    editing_enabled: bool


class PhotoMatch(str, Enum):
    EXACT = "exact"
    OUTDATED_MINOR = "outdated_minor"
    NOT_MATCHING = "not_matching"


class AmenitiesState(str, Enum):
    ALL_WORK = "all_work"
    SOME_NOT_WORKING = "some_not_working"
    EXTRA_NOT_LISTED = "extra_not_listed"


class WaitTime(str, Enum):
    INSTANT = "instant"
    UP_TO_10 = "up_to_10"
    FROM_10_TO_30 = "from_10_to_30"
    OVER_30 = "over_30"


class Informedness(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NOT_INFORMED = "not_informed"


class ProblemResolution(str, Enum):
    EFFECTIVE = "effective"
    PARTIAL = "partial"
    NONE = "none"


class WifiQuality(str, Enum):
    STABLE_FAST = "stable_fast"
    INTERMITTENT = "intermittent"
    VERY_SLOW = "very_slow"
    ABSENT = "absent"


class AcState(str, Enum):
    WORKS = "works"
    NOISY = "noisy"
    NOT_WORKING = "not_working"


class PlumbingState(str, Enum):
    OK = "ok"
    LEAKS = "leaks"
    NOT_WORKING = "not_working"


class FurnitureState(str, Enum):
    NEW = "new"
    SLIGHTLY_WORN = "slightly_worn"
    NEEDS_REPLACEMENT = "needs_replacement"


class FoodMatch(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    NOT_MATCH = "not_match"


class FoodAssortment(str, Enum):
    RICH = "rich"
    STANDARD = "standard"
    MODEST = "modest"


class FireAlarm(str, Enum):
    YES = "yes"
    NO = "no"
    NOT_NOTICED = "not_noticed"


class ExitsState(str, Enum):
    CLEAR = "clear"
    OBSTRUCTED = "obstructed"


class SafeState(str, Enum):
    WORKS = "works"
    NOT_WORKING = "not_working"
    ABSENT = "absent"


class ReportStep1Payload(BaseModel):
    photo_match: PhotoMatch
    photo_mismatch_text: str | None = Field(default=None, min_length=5, max_length=2000)
    amenities_state: AmenitiesState
    amenities_details: str | None = Field(default=None, min_length=5, max_length=2000)
    room_cleanliness: int = Field(ge=1, le=10)
    bathroom_sanitation: int = Field(ge=1, le=10)
    linen_freshness: int = Field(ge=1, le=10)
    public_area_cleanliness: int = Field(ge=1, le=10)

    @field_validator("photo_mismatch_text", "amenities_details", mode="before")
    @classmethod
    def strip_empty_optional(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def validate_conditionals(self) -> "ReportStep1Payload":
        if self.photo_match is PhotoMatch.NOT_MATCHING and not self.photo_mismatch_text:
            raise ValueError("Укажите детали несоответствия фотографий")
        if (
            self.amenities_state in {AmenitiesState.SOME_NOT_WORKING, AmenitiesState.EXTRA_NOT_LISTED}
            and not self.amenities_details
        ):
            raise ValueError("Укажите детали по удобствам")
        return self


class ReportStep2Payload(BaseModel):
    wait_time: WaitTime
    politeness: int = Field(ge=1, le=10)
    informedness: Informedness
    response_speed: int = Field(ge=1, le=10)
    problem_resolution: ProblemResolution
    wifi_quality: WifiQuality
    ac_state: AcState
    plumbing_state: PlumbingState
    furniture_state: FurnitureState
    food_match: FoodMatch
    food_quality: int = Field(ge=1, le=10)
    food_assortment: FoodAssortment
    fire_alarm: FireAlarm | None = None
    exits_state: ExitsState | None = None
    safe_state: SafeState | None = None

#Пусть будет шесть
class ReportStep6Payload(BaseModel):
    liked: str = Field(min_length=50, max_length=2000)
    to_improve: str = Field(min_length=50, max_length=2000)
    advantages: str = Field(min_length=50, max_length=2000)
    confirmed: bool

    @model_validator(mode="after")
    def ensure_confirmed(self) -> "ReportStep6Payload":
        if not self.confirmed:
            raise ValueError("Необходимо подтвердить достоверность отчета")
        return self


class ReportPhotoRead(BaseModel):
    id: int
    report_id: str
    section: PhotoSection
    filename: str
    path: str
    mime: str | None = None
    size: int | None = None
    created_at: datetime
    url: str