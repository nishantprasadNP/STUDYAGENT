"""Next work: proposed schedule revisions and their individual changes."""

from datetime import date, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UTCDateTime, enum_col
from app.models.enums import ChangeType, RevisionStatus, RevisionTrigger


class ScheduleRevision(TimestampMixin, Base):
    __tablename__ = "schedule_revisions"
    __table_args__ = (sa.Index("ix_schedule_revisions_status", "status"),)

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(sa.ForeignKey("study_plans.id"))
    base_plan_version: Mapped[int] = mapped_column(sa.Integer)
    status: Mapped[RevisionStatus] = mapped_column(
        enum_col(RevisionStatus), default=RevisionStatus.PROPOSED
    )
    trigger: Mapped[RevisionTrigger] = mapped_column(enum_col(RevisionTrigger))
    reason: Mapped[str] = mapped_column(sa.Text)
    validation: Mapped[dict[str, Any]] = mapped_column(sa.JSON, default=dict)
    presented_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class RevisionChange(TimestampMixin, Base):
    __tablename__ = "revision_changes"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    revision_id: Mapped[int] = mapped_column(
        sa.ForeignKey("schedule_revisions.id", ondelete="CASCADE")
    )
    change_type: Mapped[ChangeType] = mapped_column(enum_col(ChangeType))
    task_id: Mapped[int | None] = mapped_column(sa.ForeignKey("tasks.id"))
    topic_id: Mapped[int] = mapped_column(sa.ForeignKey("topics.id"))
    from_date: Mapped[date | None] = mapped_column(sa.Date)
    to_date: Mapped[date | None] = mapped_column(sa.Date)
    from_problems: Mapped[int | None] = mapped_column(sa.Integer)
    to_problems: Mapped[int | None] = mapped_column(sa.Integer)
    from_minutes: Mapped[int | None] = mapped_column(sa.Integer)
    to_minutes: Mapped[int | None] = mapped_column(sa.Integer)
