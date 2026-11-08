from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.profile import ProfileOut, ProfilePatch, ProfileResponse
from app.services import profile as profile_service

router = APIRouter(prefix="/profile", tags=["profile"])

Db = Annotated[Session, Depends(get_db)]


@router.get("", response_model=ProfileOut)
def read_profile(db: Db) -> ProfileOut:
    return profile_service.get_profile(db)


@router.patch("", response_model=ProfileResponse)
def patch_profile(patch: ProfilePatch, db: Db) -> ProfileResponse:
    return profile_service.update_profile(db, patch)
