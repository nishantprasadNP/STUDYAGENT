"""Planned work: study plans and their tasks."""

from datetime import date

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, enum_col
from app.models.enums import PlanStatus, TaskStatus


class StudyPlan(TimestampMixin, Base):
    __tablename__ = "study_plans"
    __table_args__ = (
        sa.CheckConstraint("end_date >= start_date", name="date_range"),
        sa.Index(
            "uq_study_plans_one_active",
            "status",
            unique=True,
            sqlite_where=sa.text("status = 'active'"),
        ),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    version: Mapped[int] = mapped_column(sa.Integer, default=1)
    status: Mapped[PlanStatus] = mapped_column(enum_col(PlanStatus))
    start_date: Mapped[date] = mapped_column(sa.Date)
    end_date: Mapped[date] = mapped_column(sa.Date)
    rationale: Mapped[str | None] = mapped_column(sa.Text)


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        sa.CheckConstraint("planned_problems > 0", name="planned_problems_positive"),
        sa.CheckConstraint(
            "completed_problems BETWEEN 0 AND planned_problems", name="completed_problems_range"
        ),
        sa.CheckConstraint("planned_minutes > 0", name="planned_minutes_positive"),
        sa.Index("ix_tasks_scheduled_date", "scheduled_date"),
        sa.Index("ix_tasks_plan_id_scheduled_date", "plan_id", "scheduled_date"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(sa.ForeignKey("study_plans.id"))
    topic_id: Mapped[int] = mapped_column(sa.ForeignKey("topics.id"))
    scheduled_date: Mapped[date] = mapped_column(sa.Date)
    order_in_day: Mapped[int] = mapped_column(sa.Integer, default=0)
    title: Mapped[str] = mapped_column(sa.String(200))
    planned_problems: Mapped[int] = mapped_column(sa.Integer)
    completed_problems: Mapped[int] = mapped_column(sa.Integer, default=0)
    planned_minutes: Mapped[int] = mapped_column(sa.Integer)
    status: Mapped[TaskStatus] = mapped_column(enum_col(TaskStatus), default=TaskStatus.PENDING)
    carried_from_task_id: Mapped[int | None] = mapped_column(sa.ForeignKey("tasks.id"))
    # No FK cycle: schedule_revisions references study_plans, not tasks, so no use_alter.
    created_by_revision_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("schedule_revisions.id")
    )
