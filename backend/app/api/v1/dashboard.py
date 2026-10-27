"""Dashboard aggregation for the authenticated home."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import (
    AnalysisRun,
    Application,
    MatchReport,
    Profile,
    ProjectPlan,
    Resume,
    Roadmap,
    RoadmapMilestone,
    SavedJob,
    User,
)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    resumes = db.scalars(
        select(Resume).where(Resume.user_id == user.id, Resume.is_archived.is_(False)).order_by(Resume.updated_at.desc())
    ).all()
    latest_analysis = db.scalar(
        select(AnalysisRun).where(AnalysisRun.user_id == user.id).order_by(AnalysisRun.created_at.desc())
    )
    latest_match = db.scalar(
        select(MatchReport).where(MatchReport.user_id == user.id).order_by(MatchReport.created_at.desc())
    )
    roadmap = db.scalar(select(Roadmap).where(Roadmap.user_id == user.id).order_by(Roadmap.created_at.desc()))
    pending_milestones = 0
    active_projects = db.scalar(select(func.count()).select_from(ProjectPlan).where(ProjectPlan.user_id == user.id, ProjectPlan.status != "done")) or 0
    if roadmap:
        pending_milestones = db.scalar(
            select(func.count()).select_from(RoadmapMilestone).where(
                RoadmapMilestone.roadmap_id == roadmap.id, RoadmapMilestone.status != "done"
            )
        ) or 0
    saved = db.scalar(select(func.count()).select_from(SavedJob).where(SavedJob.user_id == user.id)) or 0
    applications = db.scalar(select(func.count()).select_from(Application).where(Application.user_id == user.id)) or 0

    next_actions: list[dict] = []
    if not resumes:
        next_actions.append({"label": "Upload or create your first resume", "href": "/app/resumes"})
    if profile is None or not profile.onboarding_completed:
        next_actions.append({"label": "Complete your profile", "href": "/app/onboarding"})
    if latest_analysis is None and resumes:
        next_actions.append({"label": "Run a resume quality analysis", "href": "/app/resumes"})
    if latest_match is None and resumes:
        next_actions.append({"label": "Compare your resume to a job description", "href": "/app/match"})
    if roadmap is None and resumes:
        next_actions.append({"label": "Generate a career roadmap", "href": "/app/career-roadmap"})
    if pending_milestones:
        next_actions.append({"label": f"{pending_milestones} roadmap milestone(s) remaining", "href": "/app/career-roadmap"})

    return {
        "target_role": (profile.target_roles or [None])[0] if profile and profile.target_roles else None,
        "profile_completed": bool(profile and profile.onboarding_completed),
        "resume_count": len(resumes),
        "latest_resume": (
            {"id": resumes[0].id, "title": resumes[0].title, "updated_at": resumes[0].updated_at.isoformat()}
            if resumes else None
        ),
        "latest_quality": (
            {"score": latest_analysis.overall_score, "created_at": latest_analysis.created_at.isoformat()}
            if latest_analysis else None
        ),
        "latest_match": (
            {"score": latest_match.overall_score, "created_at": latest_match.created_at.isoformat()}
            if latest_match else None
        ),
        "roadmap": (
            {"id": roadmap.id, "target_role": roadmap.target_role, "readiness_score": roadmap.readiness_score,
             "pending_milestones": pending_milestones}
            if roadmap else None
        ),
        "active_projects": active_projects,
        "saved_jobs": saved,
        "applications": applications,
        "next_actions": next_actions,
        "note": "Progress indicators reflect your actual activity. No scores are fabricated.",
    }
