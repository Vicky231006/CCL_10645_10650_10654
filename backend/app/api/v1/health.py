"""Health, readiness, and AI-provider status endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.services.ai.providers import provider_status
from app.services.parsers.registry import registered_formats

router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}


@router.get("/meta/formats")
def formats() -> dict:
    return {"formats": registered_formats(), "max_upload_mb": settings.max_upload_mb}


@router.get("/meta/ai-status")
def ai_status() -> dict:
    return provider_status()
