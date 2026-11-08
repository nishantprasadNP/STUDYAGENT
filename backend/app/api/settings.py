from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.settings import SettingsOut, SettingsPatch
from app.services import settings as settings_service

router = APIRouter(prefix="/settings", tags=["settings"])

Db = Annotated[Session, Depends(get_db)]


@router.get("", response_model=SettingsOut)
def read_settings(db: Db) -> SettingsOut:
    return settings_service.get_settings(db)


@router.patch("", response_model=SettingsOut)
def patch_settings(patch: SettingsPatch, db: Db) -> SettingsOut:
    return settings_service.update_settings(db, patch)
