"""Student profile: auto-created single row, partial updates, completeness."""

from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings as get_app_config
from app.models import StudentProfile
from app.schemas.profile import WEEKDAYS, PlanImpact, ProfileOut, ProfilePatch, ProfileResponse
from app.services.errors import ValidationFailedError
from app.services.time import today_in

PROFILE_ID = 1


def _full_week(value: dict[str, Any] | None) -> dict[str, int]:
    value = value or {}
    return {d: int(value.get(d, 0)) for d in WEEKDAYS}


def _get_or_create(db: Session) -> StudentProfile:
    row = db.get(StudentProfile, PROFILE_ID)
    if row is None:
        row = StudentProfile(
            id=PROFILE_ID,
            name="",
            timezone=get_app_config().app_timezone_fallback,
            weekly_availability=_full_week(None),
            preferences={},
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def completeness(row: StudentProfile) -> list[str]:
    """Missing required fields, in a fixed order. Empty list = complete."""
    missing: list[str] = []
    if not row.name.strip():
        missing.append("name")
    if not row.timezone:
        missing.append("timezone")
    if row.target_date is None:
        missing.append("target_date")
    if row.skill_level is None:
        missing.append("skill_level")
    if not any(v > 0 for v in _full_week(row.weekly_availability).values()):
        missing.append("weekly_availability")
    return missing


def _to_out(row: StudentProfile) -> ProfileOut:
    missing = completeness(row)
    return ProfileOut(
        id=row.id,
        name=row.name,
        timezone=row.timezone,
        goal_text=row.goal_text,
        target_date=row.target_date,
        skill_level=row.skill_level,
        weekly_availability=_full_week(row.weekly_availability),
        preferred_session_minutes=row.preferred_session_minutes,
        checkin_time=row.checkin_time,
        reminder_time=row.reminder_time,
        preferences=dict(row.preferences or {}),
        is_complete=not missing,
        missing_fields=missing,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def get_profile(db: Session) -> ProfileOut:
    return _to_out(_get_or_create(db))


def _current(row: StudentProfile, field: str) -> Any:
    if field == "weekly_availability":
        return _full_week(row.weekly_availability)
    return getattr(row, field)


def update_profile(db: Session, patch: ProfilePatch) -> ProfileResponse:
    row = _get_or_create(db)
    new: dict[str, Any] = {f: getattr(patch, f) for f in patch.model_fields_set}

    timezone: str = new.get("timezone", row.timezone)
    target = new.get("target_date")
    if target is not None and target < today_in(timezone):
        raise ValidationFailedError(
            f"target_date must be today or later in {timezone}", {"field": "target_date"}
        )

    if {"checkin_time", "reminder_time"} & new.keys():
        checkin = new.get("checkin_time", row.checkin_time)
        reminder = new.get("reminder_time", row.reminder_time)
        if not reminder > checkin:  # zero-padded HH:MM compares correctly as strings
            raise ValidationFailedError(
                "reminder_time must be later than checkin_time on the same day",
                {"field": "reminder_time"},
            )

    changed = sorted(f for f, v in new.items() if _current(row, f) != v)
    for field in changed:
        setattr(row, field, new[field])
    if changed:
        db.commit()
        db.refresh(row)
        # TODO(phase-4): reschedule check-in jobs when checkin_time / reminder_time /
        # timezone change.

    return ProfileResponse(
        profile=_to_out(row),
        changed_fields=changed,
        plan_impact=PlanImpact(
            availability_or_deadline_changed=bool(
                {"weekly_availability", "target_date"} & set(changed)
            ),
            # TODO(phase-2): validate the active plan against the new availability/deadline.
        ),
    )
