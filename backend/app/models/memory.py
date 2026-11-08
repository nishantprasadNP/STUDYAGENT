"""Agent memory: chat log, learned patterns, weekly reports and notifications."""

from datetime import date, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UTCDateTime, enum_col
from app.models.enums import MessageRole, NotificationType


class AgentMessage(TimestampMixin, Base):
    __tablename__ = "agent_messages"
    __table_args__ = (sa.Index("ix_agent_messages_created_at", "created_at"),)

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    role: Mapped[MessageRole] = mapped_column(enum_col(MessageRole))
    content: Mapped[str | None] = mapped_column(sa.Text)
    tool_name: Mapped[str | None] = mapped_column(sa.String(64))
    tool_args: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)
    tool_result: Mapped[dict[str, Any] | None] = mapped_column(sa.JSON)


class LearningPattern(TimestampMixin, Base):
    __tablename__ = "learning_patterns"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    pattern_key: Mapped[str] = mapped_column(sa.String(64), unique=True)
    value: Mapped[Any] = mapped_column(sa.JSON)
    evidence: Mapped[Any] = mapped_column(sa.JSON)
    computed_at: Mapped[datetime] = mapped_column(UTCDateTime())


class WeeklyReport(TimestampMixin, Base):
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    week_start: Mapped[date] = mapped_column(sa.Date, unique=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(sa.JSON)
    summary_text: Mapped[str | None] = mapped_column(sa.Text)


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (sa.Index("ix_notifications_read_at", "read_at"),)

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    type: Mapped[NotificationType] = mapped_column(enum_col(NotificationType))
    payload: Mapped[dict[str, Any]] = mapped_column(sa.JSON, default=dict)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
