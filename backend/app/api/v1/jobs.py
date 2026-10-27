"""Job description parsing and resume-to-job matching routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.core.errors import NotFoundError
from app.models import AuditEvent, JobDescription, KeywordEvidence, MatchReport, Resume, ResumeVersion, User
from app.schemas.common import Page
from app.schemas.job import JobCreate, JobOut, KeywordOut, MatchOut, MatchRequest
from app.services.matching.engine import extract_keywords, match_resume, parse_job

router = APIRouter(tags=["jobs"])


def _owned_job(db: Session, user: User, job_id: str) -> JobDescription:
    job = db.get(JobDescription, job_id)
    if not job or job.user_id != user.id:
        raise NotFoundError("Job description not found.")
    return job


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_job(payload: JobCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobOut:
    parsed = parse_job(payload.raw_text)
    job = JobDescription(
        user_id=user.id, title=payload.title, company=payload.company, location=payload.location,
        source_url=payload.source_url, raw_text=payload.raw_text, parsed=parsed,
        seniority=parsed.get("seniority"), opportunity_type=payload.opportunity_type,
    )
    db.add(job)
    db.add(AuditEvent(user_id=user.id, action="job.create", target_type="job", target_id=job.id))
    db.commit()
    db.refresh(job)
    return JobOut.model_validate(job)


@router.get("/jobs", response_model=Page[JobOut])
def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[JobOut]:
    total = db.scalar(select(func.count()).select_from(JobDescription).where(JobDescription.user_id == user.id))
    rows = db.scalars(
        select(JobDescription).where(JobDescription.user_id == user.id)
        .order_by(JobDescription.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return Page(items=[JobOut.model_validate(r) for r in rows], total=total or 0, limit=limit, offset=offset)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JobOut:
    return JobOut.model_validate(_owned_job(db, user, job_id))


def _build_match_out(match: MatchReport) -> MatchOut:
    return MatchOut(
        id=match.id, job_id=match.job_id, resume_id=match.resume_id, version_id=match.version_id,
        overall_score=match.overall_score, coverage=match.coverage, breakdown=match.breakdown,
        methodology=match.methodology, ai_used=match.ai_used,
        keywords=[KeywordOut.model_validate(k) for k in match.keywords], created_at=match.created_at,
    )


@router.post("/jobs/match", response_model=MatchOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_match(payload: MatchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MatchOut:
    job = _owned_job(db, user, payload.job_id)
    resume = db.get(Resume, payload.resume_id)
    if not resume or resume.user_id != user.id:
        raise NotFoundError("Resume not found.")
    version = db.get(ResumeVersion, payload.version_id) if payload.version_id else next(
        (v for v in resume.versions if v.is_primary), None
    )
    if version is None or version.resume_id != resume.id:
        raise NotFoundError("Resume version not found.")

    from app.schemas.resume import ResumeContent

    content = ResumeContent.model_validate(version.content or {})
    keywords = extract_keywords(job.raw_text)
    result = match_resume(content, keywords)

    match = MatchReport(
        user_id=user.id, job_id=job.id, resume_id=resume.id, version_id=version.id,
        overall_score=result["overall_score"], coverage=result["coverage"],
        breakdown=result["breakdown"], methodology=result["methodology"], ai_used=False,
    )
    db.add(match)
    db.flush()
    for ev in result["evidence"]:
        db.add(KeywordEvidence(match_id=match.id, **ev))
    db.add(AuditEvent(user_id=user.id, action="match.create", target_type="match", target_id=match.id,
                      detail={"score": result["overall_score"]}))
    db.commit()
    db.refresh(match)
    return _build_match_out(match)


@router.get("/matches", response_model=Page[MatchOut])
def list_matches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[MatchOut]:
    total = db.scalar(select(func.count()).select_from(MatchReport).where(MatchReport.user_id == user.id))
    rows = db.scalars(
        select(MatchReport).where(MatchReport.user_id == user.id)
        .order_by(MatchReport.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return Page(items=[_build_match_out(m) for m in rows], total=total or 0, limit=limit, offset=offset)


@router.get("/matches/{match_id}", response_model=MatchOut)
def get_match(match_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MatchOut:
    match = db.get(MatchReport, match_id)
    if not match or match.user_id != user.id:
        raise NotFoundError("Match report not found.")
    return _build_match_out(match)
