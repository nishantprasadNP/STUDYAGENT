from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.catalog import TopicOut
from app.services import catalog as catalog_service

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
def read_topics(db: Annotated[Session, Depends(get_db)]) -> list[TopicOut]:
    return catalog_service.list_topics(db)
