"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import api_router
from app.config import get_settings
from app.logging import configure_logging
from app.services.errors import DomainError

logger = logging.getLogger("studypilot")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    ZoneInfo(settings.app_timezone_fallback)  # already validated by Settings; fail fast anyway
    if settings.openai_api_key is None:
        logger.warning("OPENAI_API_KEY is not set; agent features will be unavailable")
    app.state.scheduler_status = "not_started"
    # TODO(phase-4): start APScheduler here and set scheduler_status = "running".
    logger.info(
        "startup complete",
        extra={
            "version": __version__,
            "env": settings.app_env,
            "tz": settings.app_timezone_fallback,
        },
    )
    yield
    # TODO(phase-4): shut down APScheduler and set scheduler_status = "stopped".
    logger.info("shutdown complete")


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Render DomainError as {"ok": false, "error": {code, message, details}}."""
    assert isinstance(exc, DomainError)
    return JSONResponse(status_code=exc.status_code, content=exc.to_payload())


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="StudyPilot AI", version=__version__, lifespan=lifespan)
    app.state.scheduler_status = "not_started"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(DomainError, domain_error_handler)
    app.include_router(api_router)
    return app


app = create_app()
