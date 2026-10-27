"""Application tracker routes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.core.errors import NotFoundError
from app.models import Application, User
from app.schemas.common import Page
from app.schemas.job import ApplicationCreate, ApplicationOut, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"])

VALID_STATUSES = {"saved", "applied", "interview", "offer", "rejected", "withdrawn"}


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_application(payload: ApplicationCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ApplicationOut:
    app_row = Application(
        user_id=user.id, company=payload.company, role=payload.role,
        status=payload.status if payload.status in VALID_STATUSES else "saved",
        job_url=payload.job_url, source=payload.source, resume_id=payload.resume_id,
        cover_letter=payload.cover_letter, contact_notes=payload.contact_notes,
        interview_notes=payload.interview_notes, match_id=payload.match_id, roadmap_id=payload.roadmap_id,
        saved_at=datetime.now(timezone.utc),
    )
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    return ApplicationOut.model_validate(app_row)


@router.get("", response_model=Page[ApplicationOut])
def list_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ApplicationOut]:
    stmt = select(Application).where(Application.user_id == user.id)
    if status_filter:
        stmt = stmt.where(Application.status == status_filter)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Application.company.ilike(like), Application.role.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Application.updated_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=[ApplicationOut.model_validate(r) for r in rows], total=total or 0, limit=limit, offset=offset)


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ApplicationOut:
    app_row = db.get(Application, application_id)
    if not app_row or app_row.user_id != user.id:
        raise NotFoundError("Application not found.")
    return ApplicationOut.model_validate(app_row)


@router.patch("/{application_id}", response_model=ApplicationOut, dependencies=[Depends(require_csrf)])
def update_application(application_id: str, payload: ApplicationUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ApplicationOut:
    app_row = db.get(Application, application_id)
    if not app_row or app_row.user_id != user.id:
        raise NotFoundError("Application not found.")
    data = payload.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in VALID_STATUSES:
        data.pop("status")
    for key, value in data.items():
        setattr(app_row, key, value)
    if data.get("status") == "applied" and app_row.applied_at is None:
        app_row.applied_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(app_row)
    return ApplicationOut.model_validate(app_row)


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def delete_application(application_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    app_row = db.get(Application, application_id)
    if not app_row or app_row.user_id != user.id:
        raise NotFoundError("Application not found.")
    db.delete(app_row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
