"""Profile and onboarding routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.models import Profile, User
from app.schemas.profile import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


def get_or_create_profile(db: Session, user: User) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).one_or_none()
    if profile is None:
        profile = Profile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=ProfileOut)
def read_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileOut:
    return ProfileOut.model_validate(get_or_create_profile(db, user))


@router.patch("", response_model=ProfileOut, dependencies=[Depends(require_csrf)])
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    profile = get_or_create_profile(db, user)
    data = payload.model_dump(exclude_unset=True)
    if "experience" in data and data["experience"] is not None:
        data["experience"] = [e if isinstance(e, dict) else e.model_dump() for e in payload.experience]
    if "projects" in data and data["projects"] is not None:
        data["projects"] = [p if isinstance(p, dict) else p.model_dump() for p in payload.projects]
    for key, value in data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return ProfileOut.model_validate(profile)
