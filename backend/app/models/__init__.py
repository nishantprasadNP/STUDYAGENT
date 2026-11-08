"""Import every model so Base.metadata (and therefore Alembic) sees all tables."""

from app.models.base import Base, TimestampMixin, UTCDateTime, enum_col, utcnow
from app.models.catalog import Topic, TopicPrerequisite
from app.models.memory import AgentMessage, LearningPattern, Notification, WeeklyReport
from app.models.plan import StudyPlan, Task
from app.models.profile import AppSettings, StudentProfile
from app.models.progress import CheckinTaskEntry, DailyCheckin, StudySession
from app.models.revision import RevisionChange, ScheduleRevision

__all__ = [
    "AgentMessage",
    "AppSettings",
    "Base",
    "CheckinTaskEntry",
    "DailyCheckin",
    "LearningPattern",
    "Notification",
    "RevisionChange",
    "ScheduleRevision",
    "StudentProfile",
    "StudyPlan",
    "StudySession",
    "Task",
    "TimestampMixin",
    "Topic",
    "TopicPrerequisite",
    "UTCDateTime",
    "WeeklyReport",
    "enum_col",
    "utcnow",
]
