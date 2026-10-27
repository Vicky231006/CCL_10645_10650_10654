"""AI resume tailoring with truth preservation and user approval."""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.core.errors import NotFoundError
from app.models import JobDescription, Resume, ResumeVersion, TailorSuggestion, User
from app.schemas.career import TailorApplyRequest, TailorRequest, TailorSuggestionOut
from app.schemas.resume import ResumeContent
from app.services.ai.service import ai_rewrite_bullets
from app.services.ai.truth import verify_suggestion

router = APIRouter(prefix="/tailor", tags=["tailor"])

WEAK_PREFIXES = {
    "responsible for ": "",
    "worked on ": "Developed ",
    "helped with ": "Supported ",
    "helped to ": "",
    "assisted with ": "Contributed to ",
    "participated in ": "Contributed to ",
    "involved in ": "Contributed to ",
    "tasked with ": "",
}


def _collect_bullets(content: ResumeContent) -> list[str]:
    bullets: list[str] = []
    for exp in content.experience:
        bullets += exp.bullets
    for proj in content.projects:
        bullets += proj.bullets
    return [b for b in bullets if b.strip()]


def _deterministic_rewrites(bullets: list[str]) -> list[dict]:
    """Only reword/clean existing bullets — never add facts."""
    out: list[dict] = []
    for b in bullets:
        low = b.lower()
        for prefix, replacement in WEAK_PREFIXES.items():
            if low.startswith(prefix):
                rest = b[len(prefix):]
                rest = rest[0].upper() + rest[1:] if rest else rest
                proposed = (replacement + rest).strip()
                if proposed and proposed.lower() != b.lower():
                    out.append({
                        "original": b,
                        "proposed": proposed,
                        "rationale": "Starts with a stronger, more direct verb (text unchanged otherwise).",
                    })
                break
    return out


@router.post("/suggestions", response_model=list[TailorSuggestionOut], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_csrf)])
def create_suggestions(payload: TailorRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TailorSuggestionOut]:
    resume = db.get(Resume, payload.resume_id)
    if not resume or resume.user_id != user.id:
        raise NotFoundError("Resume not found.")
    job = db.get(JobDescription, payload.job_id)
    if not job or job.user_id != user.id:
        raise NotFoundError("Job description not found.")
    version = db.get(ResumeVersion, payload.version_id) if payload.version_id else next(
        (v for v in resume.versions if v.is_primary), None
    )
    if version is None or version.resume_id != resume.id:
        raise NotFoundError("Resume version not found.")

    content = ResumeContent.model_validate(version.content or {})
    bullets = _collect_bullets(content)
    source_text = content.all_text()

    raw_suggestions: list[dict] = []
    ai_used = False
    if payload.use_ai and settings.llm_provider != "none" and bullets:
        try:
            raw_suggestions = ai_rewrite_bullets(source_text, job.raw_text, bullets[:20])
            ai_used = True
        except Exception:  # noqa: BLE001
            raw_suggestions = []
    if not raw_suggestions:
        raw_suggestions = _deterministic_rewrites(bullets)

    created: list[TailorSuggestion] = []
    for s in raw_suggestions:
        original = str(s.get("original", "")).strip()
        proposed = str(s.get("proposed", "")).strip()
        if not original or not proposed:
            continue
        verified, flags = verify_suggestion(original, proposed, source_text)
        row = TailorSuggestion(
            user_id=user.id, resume_id=resume.id, version_id=version.id, job_id=job.id,
            original=original, proposed=proposed, rationale=s.get("rationale"),
            source_excerpt=original[:300], status="pending", verified=verified, flags=flags, ai_used=ai_used,
        )
        db.add(row)
        created.append(row)
    db.commit()
    return [TailorSuggestionOut.model_validate(r) for r in created]


@router.get("/suggestions", response_model=list[TailorSuggestionOut])
def list_suggestions(
    resume_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TailorSuggestionOut]:
    stmt = select(TailorSuggestion).where(TailorSuggestion.user_id == user.id)
    if resume_id:
        stmt = stmt.where(TailorSuggestion.resume_id == resume_id)
    rows = db.scalars(stmt.order_by(TailorSuggestion.created_at.desc())).all()
    return [TailorSuggestionOut.model_validate(r) for r in rows]


@router.post("/apply", dependencies=[Depends(require_csrf)])
def apply_suggestions(payload: TailorApplyRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    applied = 0
    rejected = 0
    touched_versions: dict[str, ResumeVersion] = {}
    for sid in payload.suggestion_ids:
        row = db.get(TailorSuggestion, sid)
        if not row or row.user_id != user.id:
            continue
        if payload.accept and not row.verified:
            # never apply a suggestion that failed the truth check
            continue
        row.status = "accepted" if payload.accept else "rejected"
        if payload.accept:
            version = db.get(ResumeVersion, row.version_id)
            if version is None:
                continue
            touched_versions[version.id] = version
            content = ResumeContent.model_validate(version.content or {})
            replaced = False
            for exp in content.experience:
                content.experience  # keep ref
                for i, b in enumerate(exp.bullets):
                    if b.strip() == row.original.strip():
                        exp.bullets[i] = row.proposed
                        replaced = True
            for proj in content.projects:
                for i, b in enumerate(proj.bullets):
                    if b.strip() == row.original.strip():
                        proj.bullets[i] = row.proposed
                        replaced = True
            if replaced:
                version.content = content.model_dump()
                applied += 1
        else:
            rejected += 1
    db.commit()
    return {"applied": applied, "rejected": rejected}
