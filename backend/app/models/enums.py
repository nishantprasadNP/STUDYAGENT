"""All enumerations used by the domain models."""

from enum import StrEnum


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Difficulty(StrEnum):
    EASY = "easy"
    MODERATE = "moderate"
    DIFFICULT = "difficult"


class SessionSource(StrEnum):
    MANUAL = "manual"
    CHECKIN = "checkin"
    CHAT = "chat"


class CheckinStatus(StrEnum):
    PENDING = "pending"
    REMINDED = "reminded"
    COMPLETED = "completed"
    UNREPORTED = "unreported"


class CheckinDecision(StrEnum):
    ON_TRACK = "on_track"
    BEHIND = "behind"
    AHEAD = "ahead"
    NO_DATA = "no_data"


class RevisionStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    APPLIED = "applied"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RevisionTrigger(StrEnum):
    CHECKIN = "checkin"
    USER_REQUEST = "user_request"
    CHAT = "chat"


class ChangeType(StrEnum):
    MOVE = "move"
    RESIZE = "resize"
    ADD = "add"
    REMOVE = "remove"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class NotificationType(StrEnum):
    CHECKIN_DUE = "checkin_due"
    CHECKIN_REMINDER = "checkin_reminder"
    REVISION_PROPOSED = "revision_proposed"
    WEEKLY_REPORT = "weekly_report"
