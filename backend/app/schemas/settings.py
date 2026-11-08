"""Tunable app settings (the single-row `settings` table)."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

Ratio = Annotated[float, Field(gt=0, le=1)]
PositiveFloat = Annotated[float, Field(gt=0)]
Count = Annotated[int, Field(strict=True, ge=1)]


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    behind_completion_threshold: float
    behind_carryover_count: int
    ahead_completion_threshold: float
    weak_topic_min_problems: int
    weak_topic_solve_ratio: float
    weak_topic_difficult_ratio: float
    max_daily_overbook_ratio: float
    revision_expiry_hours: int
    max_topics_per_day: int
    outstanding_checkin_days: int
    created_at: datetime
    updated_at: datetime


class SettingsPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    behind_completion_threshold: Ratio | None = None
    behind_carryover_count: Count | None = None
    ahead_completion_threshold: Ratio | None = None
    weak_topic_min_problems: Count | None = None
    weak_topic_solve_ratio: Ratio | None = None
    weak_topic_difficult_ratio: Ratio | None = None
    max_daily_overbook_ratio: PositiveFloat | None = None
    revision_expiry_hours: Count | None = None
    max_topics_per_day: Count | None = None
    outstanding_checkin_days: Count | None = None

    @field_validator("*")
    @classmethod
    def _not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("may not be null")
        return value
