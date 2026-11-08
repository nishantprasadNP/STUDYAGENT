"""Actual work: study sessions and daily check-ins."""

from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UTCDateTime, enum_col
from app.models.enums import CheckinDecision, CheckinStatus, Difficulty, SessionSource, TaskStatus


class StudySession(TimestampMixin, Base):
    __tablename__ = "study_sessions"
    __table_args__ = (
        sa.CheckConstraint("duration_minutes BETWEEN 1 AND 720", name="duration_range"),
        sa.CheckConstraint("problems_attempted >= 0", name="attempted_nonneg"),
        sa.CheckConstraint("problems_solved >= 0", name="solved_nonneg"),
        sa.CheckConstraint("problems_solved <= problems_attempted", name="solved_le_attempted"),
        sa.Index("ix_study_sessions_date", "date"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    date: Mapped[date] = mapped_column(sa.Date)
    topic_id: Mapped[int] = mapped_column(sa.ForeignKey("topics.id"))
    task_id: Mapped[int | None] = mapped_column(sa.ForeignKey("tasks.id", ondelete="SET NULL"))
    duration_minutes: Mapped[int] = mapped_column(sa.Integer)
    problems_attempted: Mapped[int] = mapped_column(sa.Integer)
    problems_solved: Mapped[int] = mapped_column(sa.Integer)
    difficulty: Mapped[Difficulty | None] = mapped_column(enum_col(Difficulty))
    notes: Mapped[str | None] = mapped_column(sa.Text)
    source: Mapped[SessionSource] = mapped_column(enum_col(SessionSource))


class DailyCheckin(TimestampMixin, Base):
    __tablename__ = "daily_checkins"
    __table_args__ = (
        sa.CheckConstraint(
            "completion_rate IS NULL OR (completion_rate >= 0 AND completion_rate <= 1)",
            name="completion_rate_range",
        ),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    date: Mapped[date] = mapped_column(sa.Date, unique=True)
    status: Mapped[CheckinStatus] = mapped_column(enum_col(CheckinStatus))
    total_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    overall_difficulty: Mapped[Difficulty | None] = mapped_column(enum_col(Difficulty))
    notes: Mapped[str | None] = mapped_column(sa.Text)
    completion_rate: Mapped[float | None] = mapped_column(sa.Float)
    decision: Mapped[CheckinDecision | None] = mapped_column(enum_col(CheckinDecision))
    prompted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    reminded_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class CheckinTaskEntry(TimestampMixin, Base):
    __tablename__ = "checkin_task_entries"
    __table_args__ = (
        sa.UniqueConstraint("checkin_id", "task_id"),
        sa.CheckConstraint("reported_completed_problems >= 0", name="reported_nonneg"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    checkin_id: Mapped[int] = mapped_column(sa.ForeignKey("daily_checkins.id", ondelete="CASCADE"))
    task_id: Mapped[int] = mapped_column(sa.ForeignKey("tasks.id"))
    reported_completed_problems: Mapped[int] = mapped_column(sa.Integer)
    reported_status: Mapped[TaskStatus] = mapped_column(enum_col(TaskStatus))
