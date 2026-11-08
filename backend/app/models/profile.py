"""Single-row tables: the student profile and tunable app settings."""

from datetime import date
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, enum_col
from app.models.enums import SkillLevel


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profile"
    __table_args__ = (sa.CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(100))
    timezone: Mapped[str] = mapped_column(sa.String(64))
    goal_text: Mapped[str | None] = mapped_column(sa.Text)
    target_date: Mapped[date | None] = mapped_column(sa.Date)
    skill_level: Mapped[SkillLevel | None] = mapped_column(enum_col(SkillLevel))
    # Shape: {"mon": 120, "tue": 90, ...} minutes per weekday.
    weekly_availability: Mapped[dict[str, Any]] = mapped_column(sa.JSON, default=dict)
    preferred_session_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    checkin_time: Mapped[str] = mapped_column(sa.String(5), default="21:00")
    reminder_time: Mapped[str] = mapped_column(sa.String(5), default="22:30")
    preferences: Mapped[dict[str, Any]] = mapped_column(sa.JSON, default=dict)


class AppSettings(TimestampMixin, Base):
    __tablename__ = "settings"
    __table_args__ = (sa.CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    behind_completion_threshold: Mapped[float] = mapped_column(
        sa.Float, server_default=sa.text("0.70")
    )
    behind_carryover_count: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("2"))
    ahead_completion_threshold: Mapped[float] = mapped_column(
        sa.Float, server_default=sa.text("1.00")
    )
    weak_topic_min_problems: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("5"))
    weak_topic_solve_ratio: Mapped[float] = mapped_column(sa.Float, server_default=sa.text("0.60"))
    weak_topic_difficult_ratio: Mapped[float] = mapped_column(
        sa.Float, server_default=sa.text("0.50")
    )
    max_daily_overbook_ratio: Mapped[float] = mapped_column(
        sa.Float, server_default=sa.text("1.00")
    )
    revision_expiry_hours: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("24"))
    max_topics_per_day: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("2"))
    outstanding_checkin_days: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("3"))
