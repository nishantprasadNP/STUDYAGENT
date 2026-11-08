"""DSA topic catalog and prerequisite graph."""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Topic(TimestampMixin, Base):
    __tablename__ = "topics"
    __table_args__ = (
        sa.CheckConstraint("difficulty_tier BETWEEN 1 AND 3", name="difficulty_tier"),
    )

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(sa.String(64), unique=True)
    name: Mapped[str] = mapped_column(sa.String(120))
    category: Mapped[str] = mapped_column(sa.String(64))
    order_index: Mapped[int] = mapped_column(sa.Integer)
    default_problem_count: Mapped[int] = mapped_column(sa.Integer)
    est_minutes_per_problem: Mapped[int] = mapped_column(sa.Integer)
    difficulty_tier: Mapped[int] = mapped_column(sa.Integer)


class TopicPrerequisite(Base):
    __tablename__ = "topic_prerequisites"
    __table_args__ = (sa.CheckConstraint("topic_id != prerequisite_topic_id", name="not_self"),)

    topic_id: Mapped[int] = mapped_column(
        sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    prerequisite_topic_id: Mapped[int] = mapped_column(
        sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
