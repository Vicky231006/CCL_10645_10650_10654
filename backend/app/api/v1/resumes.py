"""Resume upload, CRUD, versioning, analysis, and export routes."""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.core.errors import NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.models import (
    AnalysisFinding,
    AnalysisRun,
    AuditEvent,
    Resume,
    ResumeVersion,
    UploadedFile,
    User,
)
from app.schemas.common import Page
from app.schemas.resume import (
    AnalysisOut,
    AnalyzeRequest,
    ExportRequest,
    FindingOut,
    ResumeCreate,
    ResumeOut,
    ResumeUpdate,
    ResumeVersionOut,
    UploadOut,
)
from app.services.exports.service import export_resume
from app.services.parsers.base import detect_format
from app.services.parsers.registry import parse_document
from app.services.parsers.structuring import structure_text
from app.services.ai.providers import get_provider
from app.services.ai.service import ai_quality_commentary
from app.services.quality.engine import analyze_quality
from app.services.storage import new_object_key, sha256_hex, storage

logger = get_logger("resumo.resumes")
router = APIRouter(prefix="/resumes", tags=["resumes"])

ALLOWED_FORMATS = {"pdf", "docx", "doc", "txt", "md", "rtf", "odt", "tex", "html", "image"}


def _owned_resume(db: Session, user: User, resume_id: str) -> Resume:
    resume = db.get(Resume, resume_id)
    if not resume or resume.user_id != user.id:
        raise NotFoundError("Resume not found.")
    return resume


def _primary_version(resume: Resume) -> ResumeVersion | None:
    for v in resume.versions:
        if v.is_primary:
            return v
    return resume.versions[-1] if resume.versions else None


def _version_out(version: ResumeVersion) -> ResumeVersionOut:
    return ResumeVersionOut.model_validate(version)


def _resume_out(resume: Resume) -> ResumeOut:
    latest = _primary_version(resume)
    return ResumeOut(
        id=resume.id,
        title=resume.title,
        origin=resume.origin,
        template=resume.template,
        page_size=resume.page_size,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        latest_version=_version_out(latest) if latest else None,
    )


@router.get("", response_model=Page[ResumeOut])
def list_resumes(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ResumeOut]:
    total = db.scalar(select(func.count()).select_from(Resume).where(Resume.user_id == user.id, Resume.is_archived.is_(False)))
    rows = db.scalars(
        select(Resume).where(Resume.user_id == user.id, Resume.is_archived.is_(False))
        .order_by(Resume.updated_at.desc()).limit(limit).offset(offset)
    ).all()
    return Page(items=[_resume_out(r) for r in rows], total=total or 0, limit=limit, offset=offset)


@router.post("", response_model=ResumeOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_resume(payload: ResumeCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResumeOut:
    resume = Resume(user_id=user.id, title=payload.title, origin="builder", page_size=payload.page_size)
    db.add(resume)
    db.flush()
    content = payload.content.model_dump() if payload.content else {}
    version = ResumeVersion(resume_id=resume.id, version_number=1, label="Draft", content=content, is_primary=True)
    db.add(version)
    db.add(AuditEvent(user_id=user.id, action="resume.create", target_type="resume", target_id=resume.id))
    db.commit()
    db.refresh(resume)
    return _resume_out(resume)


@router.post("/upload", response_model=UploadOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
async def upload_resume(
    file: UploadFile = File(...),
    title: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadOut:
    data = await file.read()
    if not data:
        raise ValidationAppError("Uploaded file is empty.")
    if len(data) > settings.max_upload_bytes:
        raise ValidationAppError(f"File exceeds the {settings.max_upload_mb} MB limit.", code="too_large")

    filename = file.filename or "resume"
    fmt = detect_format(filename, file.content_type, data)
    if fmt not in ALLOWED_FORMATS:
        raise ValidationAppError(
            f"Unsupported file type '{fmt}'. Allowed: {', '.join(sorted(ALLOWED_FORMATS))}.",
            code="unsupported_format",
        )

    parsed = parse_document(fmt, data)
    content, structure_confidence = structure_text(parsed.text, contact_links=parsed.links)
    confidence = round(min(parsed.confidence, structure_confidence) if parsed.text else 0.0, 2)

    key = new_object_key(user.id, "resumes", filename)
    storage.put_bytes(key, data, file.content_type)

    resume = Resume(user_id=user.id, title=title or filename.rsplit(".", 1)[0][:200] or "Resume", origin="upload")
    db.add(resume)
    db.flush()
    version = ResumeVersion(
        resume_id=resume.id, version_number=1, label="Original upload",
        content=content.model_dump(), source_format=fmt, parse_confidence=confidence, is_primary=True,
    )
    db.add(version)
    db.add(
        UploadedFile(
            user_id=user.id, resume_id=resume.id, original_filename=filename,
            content_type=file.content_type, size_bytes=len(data), storage_key=key,
            sha256=sha256_hex(data), detected_format=fmt,
            status="parsed" if parsed.text else "stored",
            notes="; ".join(parsed.warnings) if parsed.warnings else None,
        )
    )
    db.add(AuditEvent(user_id=user.id, action="resume.upload", target_type="resume", target_id=resume.id,
                      detail={"format": fmt, "size": len(data)}))
    db.commit()

    from app.services.jobs import run_job
    run_job(lambda: None)  # parse already done synchronously; hook for heavy post-processing

    return UploadOut(
        resume_id=resume.id, version_id=version.id, detected_format=fmt,
        parse_confidence=confidence, warnings=parsed.warnings + parsed.notes,
        content=content,
    )


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResumeOut:
    return _resume_out(_owned_resume(db, user, resume_id))


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionOut])
def list_versions(resume_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ResumeVersionOut]:
    resume = _owned_resume(db, user, resume_id)
    return [_version_out(v) for v in resume.versions]


@router.patch("/{resume_id}", response_model=ResumeOut, dependencies=[Depends(require_csrf)])
def update_resume(
    resume_id: str,
    payload: ResumeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResumeOut:
    resume = _owned_resume(db, user, resume_id)
    if payload.title is not None:
        resume.title = payload.title
    if payload.page_size is not None:
        resume.page_size = payload.page_size
    if payload.content is not None:
        version = _primary_version(resume)
        if version is None:
            version = ResumeVersion(resume_id=resume.id, version_number=1, is_primary=True)
            db.add(version)
            db.flush()
        if payload.create_version:
            next_num = max((v.version_number for v in resume.versions), default=0) + 1
            new_version = ResumeVersion(
                resume_id=resume.id, version_number=next_num,
                label=payload.label or f"Version {next_num}",
                content=payload.content.model_dump(), is_primary=True,
            )
            for v in resume.versions:
                v.is_primary = False
            db.add(new_version)
        else:
            version.content = payload.content.model_dump()
            if payload.label:
                version.label = payload.label
    db.add(AuditEvent(user_id=user.id, action="resume.update", target_type="resume", target_id=resume.id))
    db.commit()
    db.refresh(resume)
    return _resume_out(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def delete_resume(resume_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    resume = _owned_resume(db, user, resume_id)
    for f in db.scalars(select(UploadedFile).where(UploadedFile.resume_id == resume.id)).all():
        try:
            storage.delete(f.storage_key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("storage delete failed", extra={"extra_fields": {"error": str(exc)}})
        db.delete(f)
    db.add(AuditEvent(user_id=user.id, action="resume.delete", target_type="resume", target_id=resume.id))
    db.delete(resume)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{resume_id}/duplicate", response_model=ResumeOut, dependencies=[Depends(require_csrf)])
def duplicate_resume(resume_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ResumeOut:
    resume = _owned_resume(db, user, resume_id)
    clone = Resume(user_id=user.id, title=f"{resume.title} (copy)", origin=resume.origin, page_size=resume.page_size)
    db.add(clone)
    db.flush()
    source = _primary_version(resume)
    db.add(ResumeVersion(
        resume_id=clone.id, version_number=1, label="Copy",
        content=source.content if source else {}, is_primary=True,
    ))
    db.commit()
    db.refresh(clone)
    return _resume_out(clone)


@router.post("/{resume_id}/analyze", response_model=AnalysisOut, dependencies=[Depends(require_csrf)])
def analyze_resume(
    resume_id: str,
    payload: AnalyzeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisOut:
    resume = _owned_resume(db, user, resume_id)
    version = _primary_version(resume)
    if version is None:
        raise NotFoundError("Resume has no content to analyze.")
    from app.schemas.resume import ResumeContent

    content = ResumeContent.model_validate(version.content or {})
    result = analyze_quality(content, target_role=payload.target_role)

    ai_used = False
    ai_commentary = None
    if payload.use_ai and settings.llm_provider != "none":
        try:
            commentary = ai_quality_commentary(content.all_text(), payload.target_role)
            ai_commentary = commentary.get("summary") if isinstance(commentary, dict) else str(commentary)
            if isinstance(commentary, dict):
                ai_commentary = (
                    "Strengths:\n- " + "\n- ".join(commentary.get("strengths", []))
                    + "\n\nWeaknesses:\n- " + "\n- ".join(commentary.get("weaknesses", []))
                    + "\n\nTop actions:\n- " + "\n- ".join(commentary.get("top_actions", []))
                )
            ai_used = True
        except Exception as exc:  # noqa: BLE001
            ai_commentary = f"AI commentary unavailable: {exc}"

    run = AnalysisRun(
        user_id=user.id, resume_id=resume.id, version_id=version.id, kind="quality",
        overall_score=result.overall_score, category_scores=result.category_scores,
        methodology=result.methodology, ai_used=ai_used, ai_commentary=ai_commentary,
    )
    db.add(run)
    db.flush()
    for f in result.findings:
        db.add(AnalysisFinding(
            run_id=run.id, category=f.category, severity=f.severity, source="rule",
            title=f.title, excerpt=f.excerpt, explanation=f.explanation, suggestion=f.suggestion, location=f.location,
        ))
    db.add(AuditEvent(user_id=user.id, action="resume.analyze", target_type="resume", target_id=resume.id,
                      detail={"score": result.overall_score}))
    db.commit()
    db.refresh(run)
    return AnalysisOut(
        id=run.id, resume_id=run.resume_id, version_id=run.version_id, overall_score=run.overall_score,
        category_scores=run.category_scores, methodology=run.methodology, ai_used=run.ai_used,
        ai_commentary=run.ai_commentary,
        findings=[FindingOut.model_validate(f) for f in run.findings], created_at=run.created_at,
    )


@router.get("/{resume_id}/analyses", response_model=list[AnalysisOut])
def list_analyses(resume_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AnalysisOut]:
    resume = _owned_resume(db, user, resume_id)
    runs = db.scalars(
        select(AnalysisRun).where(AnalysisRun.resume_id == resume.id).order_by(AnalysisRun.created_at.desc()).limit(20)
    ).all()
    return [
        AnalysisOut(
            id=r.id, resume_id=r.resume_id, version_id=r.version_id, overall_score=r.overall_score,
            category_scores=r.category_scores, methodology=r.methodology, ai_used=r.ai_used,
            ai_commentary=r.ai_commentary,
            findings=[FindingOut.model_validate(f) for f in r.findings], created_at=r.created_at,
        )
        for r in runs
    ]


@router.post("/{resume_id}/export", dependencies=[Depends(require_csrf)])
def export_resume_endpoint(
    resume_id: str,
    payload: ExportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    resume = _owned_resume(db, user, resume_id)
    version = db.get(ResumeVersion, payload.version_id) if payload.version_id else _primary_version(resume)
    if version is None or version.resume_id != resume.id:
        raise NotFoundError("Resume version not found.")
    from app.schemas.resume import ResumeContent

    content = ResumeContent.model_validate(version.content or {})
    try:
        data, ext, content_type = export_resume(content, payload.format, payload.page_size or resume.page_size)
    except ValueError as exc:
        raise ValidationAppError(str(exc), code="bad_format") from exc
    safe_title = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in resume.title)[:80].strip() or "resume"
    db.add(AuditEvent(user_id=user.id, action="resume.export", target_type="resume", target_id=resume.id,
                      detail={"format": ext}))
    db.commit()
    headers = {"Content-Disposition": f'attachment; filename="{safe_title}.{ext}"'}
    return Response(content=data, media_type=content_type, headers=headers)
