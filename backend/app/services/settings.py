"""Tunable thresholds (single `settings` row, auto-created with server defaults)."""

from sqlalchemy.orm import Session

from app.models import AppSettings
from app.schemas.settings import SettingsOut, SettingsPatch
from app.services.errors import ValidationFailedError

SETTINGS_ID = 1


def _get_or_create(db: Session) -> AppSettings:
    row = db.get(AppSettings, SETTINGS_ID)
    if row is None:
        row = AppSettings(id=SETTINGS_ID)
        db.add(row)
        db.commit()
        db.refresh(row)  # load the server defaults
    return row


def get_settings(db: Session) -> SettingsOut:
    return SettingsOut.model_validate(_get_or_create(db))


def update_settings(db: Session, patch: SettingsPatch) -> SettingsOut:
    row = _get_or_create(db)
    new = {f: getattr(patch, f) for f in patch.model_fields_set}

    behind = new.get("behind_completion_threshold", row.behind_completion_threshold)
    ahead = new.get("ahead_completion_threshold", row.ahead_completion_threshold)
    if behind > ahead:
        field = (
            "behind_completion_threshold"
            if "behind_completion_threshold" in new
            else "ahead_completion_threshold"
        )
        raise ValidationFailedError(
            "behind_completion_threshold must be <= ahead_completion_threshold",
            {"field": field},
        )

    changed = [f for f, v in new.items() if getattr(row, f) != v]
    for field in changed:
        setattr(row, field, new[field])
    if changed:
        db.commit()
        db.refresh(row)
    return SettingsOut.model_validate(row)
