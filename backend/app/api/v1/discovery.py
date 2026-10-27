"""Job discovery, recommendations, and saved jobs."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.core.errors import NotFoundError
from app.models import JobListing, Resume, SavedJob, User
from app.schemas.common import Page
from app.schemas.job import JobListingOut, JobRecommendation, SavedJobCreate, SavedJobOut
from app.services.matching.engine import extract_keywords, match_resume

router = APIRouter(tags=["discovery"])


def _listing_out(listing: JobListing) -> JobListingOut:
    return JobListingOut.model_validate(listing)


@router.get("/listings", response_model=Page[JobListingOut])
def list_listings(
    q: str | None = None,
    opportunity_type: str | None = None,
    work_arrangement: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[JobListingOut]:
    stmt = select(JobListing)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(JobListing.title.ilike(like), JobListing.company.ilike(like), JobListing.description.ilike(like)))
    if opportunity_type:
        stmt = stmt.where(JobListing.opportunity_type == opportunity_type)
    if work_arrangement:
        stmt = stmt.where(JobListing.work_arrangement == work_arrangement)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(JobListing.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=[_listing_out(r) for r in rows], total=total or 0, limit=limit, offset=offset)


@router.get("/listings/{listing_id}", response_model=JobListingOut)
def get_listing(listing_id: str, db: Session = Depends(get_db)) -> JobListingOut:
    listing = db.get(JobListing, listing_id)
    if not listing:
        raise NotFoundError("Listing not found.")
    return _listing_out(listing)


@router.get("/recommendations", response_model=list[JobRecommendation])
def recommendations(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobRecommendation]:
    resume = db.scalar(
        select(Resume).where(Resume.user_id == user.id, Resume.is_archived.is_(False)).order_by(Resume.updated_at.desc())
    )
    if not resume or not resume.versions:
        return []
    from app.schemas.resume import ResumeContent

    version = next((v for v in resume.versions if v.is_primary), resume.versions[-1])
    content = ResumeContent.model_validate(version.content or {})

    listings = db.scalars(select(JobListing)).all()
    ranked: list[JobRecommendation] = []
    for listing in listings:
        fake_jd = listing.description + "\nRequired: " + ", ".join(listing.skills or [])
        keywords = extract_keywords(fake_jd)
        if not keywords:
            keywords = [{"keyword": s, "importance": "required", "category": "skill"} for s in (listing.skills or [])]
        result = match_resume(content, keywords)
        reasons: list[str] = []
        for ev in result["evidence"]:
            if ev["status"] == "found":
                reasons.append(f"Evidenced: {ev['keyword']} ({ev['evidence_location']})")
        improvement = [
            f"Strengthen evidence for '{ev['keyword']}'" for ev in result["evidence"] if ev["status"] != "found"
        ][:5]
        ranked.append(
            JobRecommendation(
                listing=_listing_out(listing),
                match_score=result["overall_score"],
                reasons=reasons[:6],
                improvement=improvement,
            )
        )
    ranked.sort(key=lambda r: r.match_score, reverse=True)
    return ranked[:limit]


@router.post("/saved-jobs", response_model=SavedJobOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def save_job(payload: SavedJobCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SavedJobOut:
    saved = SavedJob(
        user_id=user.id, title=payload.title, company=payload.company, source_url=payload.source_url,
        job_id=payload.job_id, listing_id=payload.listing_id, note=payload.note,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return SavedJobOut.model_validate(saved)


@router.get("/saved-jobs", response_model=list[SavedJobOut])
def list_saved_jobs(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[SavedJobOut]:
    rows = db.scalars(select(SavedJob).where(SavedJob.user_id == user.id).order_by(SavedJob.created_at.desc())).all()
    return [SavedJobOut.model_validate(r) for r in rows]


@router.delete("/saved-jobs/{saved_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def delete_saved_job(saved_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    saved = db.get(SavedJob, saved_id)
    if not saved or saved.user_id != user.id:
        raise NotFoundError("Saved job not found.")
    db.delete(saved)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
