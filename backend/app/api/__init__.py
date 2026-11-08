"""HTTP API. Every router hangs off `api_router` (prefix /api)."""

from fastapi import APIRouter

from app.api import health, profile, settings, topics

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(profile.router)
api_router.include_router(settings.router)
api_router.include_router(topics.router)
