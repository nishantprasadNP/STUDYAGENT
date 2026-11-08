from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import __version__
from app.db import check_db, get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request, db: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    """Liveness + DB check. Always HTTP 200 so the UI can render a degraded state."""
    db_ok = check_db(db)
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db="ok" if db_ok else "error",
        scheduler=getattr(request.app.state, "scheduler_status", "not_started"),
        version=__version__,
    )
