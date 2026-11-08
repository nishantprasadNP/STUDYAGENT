"""Student profile API schemas."""

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.enums import SkillLevel
from app.services.time import is_valid_timezone

WEEKDAYS: tuple[str, ...] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"

# Fields that may be explicitly set to null in a PATCH. Everything else rejects null.
NULLABLE_PROFILE_FIELDS: frozenset[str] = frozenset(
    {"goal_text", "target_date", "skill_level", "preferred_session_minutes"}
)

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
HHMM = Annotated[str, StringConstraints(pattern=TIME_PATTERN)]
DayMinutes = Annotated[int, Field(strict=True, ge=0, le=720)]


class ProfileOut(BaseModel):
    id: int
    name: str
    timezone: str
    goal_text: str | None
    target_date: date | None
    skill_level: SkillLevel | None
    weekly_availability: dict[str, int]
    preferred_session_minutes: int | None
    checkin_time: str
    reminder_time: str
    preferences: dict[str, Any]
    is_complete: bool
    missing_fields: list[str]
    created_at: datetime
    updated_at: datetime


class ProfilePatch(BaseModel):
    """Partial update. Omitted = unchanged; explicit null only for nullable fields."""

    model_config = ConfigDict(extra="forbid")

    name: Name | None = None
    timezone: str | None = None
    goal_text: Annotated[str, StringConstraints(max_length=1000)] | None = None
    target_date: date | None = None
    skill_level: SkillLevel | None = None
    weekly_availability: dict[str, DayMinutes] | None = None
    preferred_session_minutes: Annotated[int, Field(strict=True, ge=15, le=720)] | None = None
    checkin_time: HHMM | None = None
    reminder_time: HHMM | None = None
    preferences: Annotated[dict[str, Any], Field(max_length=50)] | None = None

    @field_validator(
        "name", "timezone", "weekly_availability", "checkin_time", "reminder_time", "preferences"
    )
    @classmethod
    def _not_null(cls, value: object) -> object:
        # Only runs when the field is provided (defaults are not validated).
        if value is None:
            raise ValueError("may not be null")
        return value

    @field_validator("timezone")
    @classmethod
    def _valid_timezone(cls, value: str | None) -> str | None:
        if value is not None and not is_valid_timezone(value):
            raise ValueError(f"invalid timezone: {value!r}")
        return value

    @field_validator("weekly_availability")
    @classmethod
    def _full_week(cls, value: dict[str, int] | None) -> dict[str, int] | None:
        if value is None:
            return None
        missing = [d for d in WEEKDAYS if d not in value]
        extra = sorted(k for k in value if k not in WEEKDAYS)
        if missing or extra:
            parts = []
            if missing:
                parts.append(f"missing days: {', '.join(missing)}")
            if extra:
                parts.append(f"unknown keys: {', '.join(extra)}")
            raise ValueError(
                f"weekly_availability needs exactly {', '.join(WEEKDAYS)} ({'; '.join(parts)})"
            )
        if not any(value[d] > 0 for d in WEEKDAYS):
            raise ValueError("at least one day must have more than 0 minutes")
        return {d: value[d] for d in WEEKDAYS}


class PlanImpact(BaseModel):
    availability_or_deadline_changed: bool
    active_plan_now_invalid: bool = False  # TODO(phase-2): check the active plan
    violations: list[dict[str, Any]] = Field(default_factory=list)  # TODO(phase-2)


class ProfileResponse(BaseModel):
    profile: ProfileOut
    changed_fields: list[str]
    plan_impact: PlanImpact
