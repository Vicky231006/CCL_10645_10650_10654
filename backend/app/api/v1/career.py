"""Career development routes: roadmaps, milestones, projects, portfolio, generated assets."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.core.errors import NotFoundError, ValidationAppError
from app.models import (
    GeneratedAsset,
    JobDescription,
    LearningResource,
    PortfolioPage,
    ProjectEvidence,
    ProjectPlan,
    Resume,
    Roadmap,
    RoadmapMilestone,
    User,
)
from app.schemas.career import (
    AssetGenerateRequest,
    AssetUpdate,
    GeneratedAssetOut,
    MilestoneOut,
    MilestoneUpdate,
    PortfolioPageOut,
    PortfolioUpdate,
    ProjectEvidenceCreate,
    ProjectEvidenceOut,
    ProjectPlanCreate,
    ProjectPlanOut,
    RoadmapCreate,
    RoadmapOut,
)
from app.schemas.common import Page
from app.schemas.resume import ResumeContent
from app.services.ai.service import ai_gap_analysis, ai_generate_asset, ai_project_plan
from app.services.career.planner import build_project_plan, default_roadmap_milestones
from app.services.career.resources import resources_for
from app.services.matching.engine import extract_keywords, match_resume

router = APIRouter(tags=["career"])


def _primary_content(resume: Resume) -> ResumeContent:
    version = next((v for v in resume.versions if v.is_primary), resume.versions[-1] if resume.versions else None)
    if version is None:
        raise ValidationAppError("Resume has no content.")
    return ResumeContent.model_validate(version.content or {})


def _gap_report(content: ResumeContent, job_text: str) -> tuple[dict, float]:
    keywords = extract_keywords(job_text)
    result = match_resume(content, keywords)
    demonstrated = [e["keyword"] for e in result["evidence"] if e["status"] == "found"]
    missing_required = [e["keyword"] for e in result["evidence"] if e["status"] == "missing" and e["importance"] == "required"]
    missing_valuable = [
        e["keyword"] for e in result["evidence"]
        if e["status"] in ("missing", "weak") and e["importance"] in ("preferred", "bonus")
    ]
    report = {
        "demonstrated": demonstrated,
        "missing_required": missing_required,
        "missing_valuable": missing_valuable,
        "coverage": result["coverage"],
        "breakdown": result["breakdown"],
    }
    return report, result["overall_score"]


def _roadmap_out(roadmap: Roadmap) -> RoadmapOut:
    return RoadmapOut(
        id=roadmap.id, target_role=roadmap.target_role, company=roadmap.company,
        readiness_score=roadmap.readiness_score, summary=roadmap.summary, gap_report=roadmap.gap_report,
        ai_used=roadmap.ai_used,
        milestones=[
            MilestoneOut(
                id=m.id, position=m.position, title=m.title, kind=m.kind, week=m.week,
                estimated_hours=m.estimated_hours, rationale=m.rationale, source_requirement=m.source_requirement,
                status=m.status, evidence_url=m.evidence_url, notes=m.notes,
                resources=[
                    {"id": r.id, "title": r.title, "url": r.url, "kind": r.kind, "provider": r.provider, "is_free": r.is_free}
                    for r in m.resources
                ],
            )
            for m in roadmap.milestones
        ],
        created_at=roadmap.created_at,
    )


@router.post("/roadmaps", response_model=RoadmapOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_roadmap(payload: RoadmapCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> RoadmapOut:
    resume = db.get(Resume, payload.resume_id) if payload.resume_id else db.scalar(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.updated_at.desc())
    )
    if not resume or resume.user_id != user.id:
        raise NotFoundError("Resume not found. Upload or create a resume first.")
    job = db.get(JobDescription, payload.job_id) if payload.job_id else None
    if job and job.user_id != user.id:
        raise NotFoundError("Job description not found.")

    content = _primary_content(resume)
    job_text = job.raw_text if job else f"Target role: {payload.target_role}"
    report, readiness = _gap_report(content, job_text)

    summary = None
    ai_used = False
    milestones_data = None
    if payload.use_ai and settings.llm_provider != "none":
        try:
            ai = ai_gap_analysis(content.all_text(), job_text)
            report.update({k: ai.get(k) for k in ("demonstrated", "missing_required", "missing_valuable", "projects_to_build", "fundamentals") if ai.get(k) is not None})
            readiness = float(ai.get("readiness_score", readiness) or readiness)
            summary = ai.get("summary")
            ai_used = True
        except Exception:  # noqa: BLE001
            ai_used = False

    roadmap = Roadmap(
        user_id=user.id, job_id=job.id if job else None, resume_id=resume.id,
        target_role=payload.target_role, company=payload.company or (job.company if job else None),
        readiness_score=readiness, summary=summary or _default_summary(report), gap_report=report, ai_used=ai_used,
    )
    db.add(roadmap)
    db.flush()

    milestones_data = milestones_data or default_roadmap_milestones(
        report.get("missing_required", []), report.get("missing_valuable", [])
    )
    for i, m in enumerate(milestones_data):
        milestone = RoadmapMilestone(
            roadmap_id=roadmap.id, position=i, title=m["title"], kind=m.get("kind", "skill"),
            week=m.get("week"), estimated_hours=m.get("estimated_hours"),
            rationale=m.get("rationale"), source_requirement=m.get("source_requirement"),
        )
        db.add(milestone)
        db.flush()
        skill_name = m["title"].split(":")[-1].strip()
        for res in resources_for(skill_name):
            db.add(LearningResource(milestone_id=milestone.id, title=res["title"], url=res["url"],
                                    kind=res.get("kind", "docs"), provider=res.get("provider"),
                                    is_free=res.get("is_free", True)))
    db.commit()
    db.refresh(roadmap)
    return _roadmap_out(roadmap)


def _default_summary(report: dict) -> str:
    return (
        f"You currently evidence {len(report.get('demonstrated', []))} of the job's key terms. "
        f"Focus first on: {', '.join(report.get('missing_required', [])[:4]) or 'building projects that evidence your skills'}. "
        "Do not attempt to learn everything in the job description; prioritise the highest-impact, achievable gaps."
    )


@router.get("/roadmaps", response_model=Page[RoadmapOut])
def list_roadmaps(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[RoadmapOut]:
    total = db.scalar(select(func.count()).select_from(Roadmap).where(Roadmap.user_id == user.id))
    rows = db.scalars(select(Roadmap).where(Roadmap.user_id == user.id).order_by(Roadmap.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=[_roadmap_out(r) for r in rows], total=total or 0, limit=limit, offset=offset)


@router.get("/roadmaps/{roadmap_id}", response_model=RoadmapOut)
def get_roadmap(roadmap_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> RoadmapOut:
    roadmap = db.get(Roadmap, roadmap_id)
    if not roadmap or roadmap.user_id != user.id:
        raise NotFoundError("Roadmap not found.")
    return _roadmap_out(roadmap)


@router.patch("/milestones/{milestone_id}", response_model=MilestoneOut, dependencies=[Depends(require_csrf)])
def update_milestone(milestone_id: str, payload: MilestoneUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MilestoneOut:
    milestone = db.get(RoadmapMilestone, milestone_id)
    if not milestone:
        raise NotFoundError("Milestone not found.")
    roadmap = db.get(Roadmap, milestone.roadmap_id)
    if not roadmap or roadmap.user_id != user.id:
        raise NotFoundError("Milestone not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(milestone, key, value)
    db.commit()
    db.refresh(milestone)
    return MilestoneOut.model_validate(milestone)


@router.post("/projects", response_model=ProjectPlanOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_project(payload: ProjectPlanCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProjectPlanOut:
    resume = db.scalar(select(Resume).where(Resume.user_id == user.id).order_by(Resume.updated_at.desc()))
    job = None
    roadmap = db.get(Roadmap, payload.roadmap_id) if payload.roadmap_id else None
    if roadmap:
        if roadmap.user_id != user.id:
            raise NotFoundError("Roadmap not found.")
        if roadmap.job_id:
            job = db.get(JobDescription, roadmap.job_id)
    resume_text = _primary_content(resume).all_text() if resume else ""
    job_text = job.raw_text if job else ""

    plan: dict | None = None
    ai_used = False
    if payload.use_ai and settings.llm_provider != "none":
        try:
            plan = ai_project_plan(resume_text, job_text, payload.title)
            ai_used = True
        except Exception:  # noqa: BLE001
            plan = None
    if plan is None:
        keywords = extract_keywords(job_text) if job_text else []
        skills = [k["keyword"] for k in keywords]
        plan = build_project_plan(payload.title, skills)

    project = ProjectPlan(
        user_id=user.id, roadmap_id=payload.roadmap_id, title=payload.title,
        problem=plan.get("problem"), required_features=plan.get("required_features", []),
        optional_features=plan.get("optional_features", []), suggested_stack=plan.get("suggested_stack", []),
        milestones=plan.get("milestones", []), acceptance_criteria=plan.get("acceptance_criteria", []),
        testing=plan.get("testing"), demonstrates=plan.get("demonstrates", []),
        evidence_to_publish=plan.get("evidence_to_publish", []), resume_guidance=plan.get("resume_guidance"),
        stretch_goals=plan.get("stretch_goals", []), ai_used=ai_used,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectPlanOut.model_validate(project)


@router.get("/projects", response_model=Page[ProjectPlanOut])
def list_projects(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[ProjectPlanOut]:
    total = db.scalar(select(func.count()).select_from(ProjectPlan).where(ProjectPlan.user_id == user.id))
    rows = db.scalars(select(ProjectPlan).where(ProjectPlan.user_id == user.id).order_by(ProjectPlan.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=[ProjectPlanOut.model_validate(r) for r in rows], total=total or 0, limit=limit, offset=offset)


@router.get("/projects/{project_id}", response_model=ProjectPlanOut)
def get_project(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProjectPlanOut:
    project = db.get(ProjectPlan, project_id)
    if not project or project.user_id != user.id:
        raise NotFoundError("Project not found.")
    return ProjectPlanOut.model_validate(project)


@router.post("/projects/{project_id}/evidence", response_model=ProjectEvidenceOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def add_evidence(project_id: str, payload: ProjectEvidenceCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProjectEvidenceOut:
    project = db.get(ProjectPlan, project_id)
    if not project or project.user_id != user.id:
        raise NotFoundError("Project not found.")
    evidence = ProjectEvidence(user_id=user.id, project_plan_id=project.id, **payload.model_dump())
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return ProjectEvidenceOut.model_validate(evidence)


@router.get("/projects/{project_id}/evidence", response_model=list[ProjectEvidenceOut])
def list_evidence(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProjectEvidenceOut]:
    project = db.get(ProjectPlan, project_id)
    if not project or project.user_id != user.id:
        raise NotFoundError("Project not found.")
    rows = db.scalars(select(ProjectEvidence).where(ProjectEvidence.project_plan_id == project.id)).all()
    return [ProjectEvidenceOut.model_validate(r) for r in rows]


# ---------------- Portfolio ----------------

@router.get("/portfolio", response_model=list[PortfolioPageOut])
def list_portfolio(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PortfolioPageOut]:
    rows = db.scalars(select(PortfolioPage).where(PortfolioPage.user_id == user.id)).all()
    return [PortfolioPageOut.model_validate(r) for r in rows]


@router.post("/portfolio", response_model=PortfolioPageOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_portfolio(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PortfolioPageOut:
    slug = f"portfolio-{user.id[:8]}"
    page = db.scalar(select(PortfolioPage).where(PortfolioPage.slug == slug))
    if page is None:
        page = PortfolioPage(user_id=user.id, slug=slug, title="My Portfolio", published=False,
                             settings={"show_email": False, "show_phone": False}, content={})
        db.add(page)
        db.commit()
        db.refresh(page)
    return PortfolioPageOut.model_validate(page)


@router.patch("/portfolio/{page_id}", response_model=PortfolioPageOut, dependencies=[Depends(require_csrf)])
def update_portfolio(page_id: str, payload: PortfolioUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PortfolioPageOut:
    page = db.get(PortfolioPage, page_id)
    if not page or page.user_id != user.id:
        raise NotFoundError("Portfolio page not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(page, key, value)
    db.commit()
    db.refresh(page)
    return PortfolioPageOut.model_validate(page)


@router.get("/portfolio/public/{slug}", response_model=PortfolioPageOut)
def public_portfolio(slug: str, db: Session = Depends(get_db)) -> PortfolioPageOut:
    page = db.scalar(select(PortfolioPage).where(PortfolioPage.slug == slug, PortfolioPage.published.is_(True)))
    if not page:
        raise NotFoundError("Portfolio not found or not published.")
    return PortfolioPageOut.model_validate(page)


# ---------------- Generated assets ----------------

@router.post("/assets/generate", response_model=GeneratedAssetOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def generate_asset(payload: AssetGenerateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GeneratedAssetOut:
    context_parts: list[str] = []
    title = payload.title or payload.kind.replace("_", " ").title()
    if payload.project_evidence_id:
        ev = db.get(ProjectEvidence, payload.project_evidence_id)
        if ev and ev.user_id == user.id:
            title = ev.title
            context_parts.append(
                f"Project: {ev.title}\nProblem: {ev.problem}\nContribution: {ev.contribution}\n"
                f"Stack: {', '.join(ev.stack or [])}\nArchitecture: {ev.architecture}\nTests: {ev.tests}\nOutcomes: {ev.outcomes}"
            )
    if payload.project_plan_id:
        plan = db.get(ProjectPlan, payload.project_plan_id)
        if plan and plan.user_id == user.id:
            title = plan.title
            context_parts.append(
                f"Project plan: {plan.title}\nProblem: {plan.problem}\nRequired features: {plan.required_features}\n"
                f"Stack: {plan.suggested_stack}"
            )
    if payload.resume_id:
        resume = db.get(Resume, payload.resume_id)
        if resume and resume.user_id == user.id:
            context_parts.append("Resume:\n" + _primary_content(resume).all_text())
    if payload.job_id:
        job = db.get(JobDescription, payload.job_id)
        if job and job.user_id == user.id:
            context_parts.append(f"Target job: {job.title} at {job.company or 'a company'}\n{job.raw_text[:2000]}")

    context = "\n\n".join(context_parts)
    if not context.strip():
        raise ValidationAppError("No verified project or resume information was provided to generate from.")

    content = ""
    ai_used = False
    if payload.use_ai and settings.llm_provider != "none":
        try:
            content = ai_generate_asset(payload.kind, context)
            ai_used = True
        except Exception as exc:  # noqa: BLE001
            content = ""
            ai_used = False
    if not content:
        content = _template_asset(payload.kind, context, user.full_name or "Candidate")

    asset = GeneratedAsset(user_id=user.id, project_plan_id=payload.project_plan_id, resume_id=payload.resume_id,
                           kind=payload.kind, title=title, content=content, ai_used=ai_used)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return GeneratedAssetOut.model_validate(asset)


def _template_asset(kind: str, context: str, name: str) -> str:
    """Deterministic fallback that assembles ONLY the user's own supplied facts."""
    if kind == "bio":
        return f"{name} is a candidate building experience in software engineering. (Edit this with your real background.)\n\nSource facts:\n{context[:800]}"
    if kind == "readme":
        return f"# Project\n\n## Overview\n{context[:500]}\n\n## Setup\n1. Clone the repository.\n2. Install dependencies.\n3. Run the app.\n\n## Notes\nAdd real screenshots and test output. Do not invent metrics."
    return (
        f"# {kind.replace('_', ' ').title()}\n\n"
        "AI generation is not enabled, so this is a structured draft built from your own inputs. "
        "Edit it and fill in only true details.\n\n"
        "## Source facts\n" + context[:1500]
    )


@router.get("/assets", response_model=Page[GeneratedAssetOut])
def list_assets(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Page[GeneratedAssetOut]:
    total = db.scalar(select(func.count()).select_from(GeneratedAsset).where(GeneratedAsset.user_id == user.id))
    rows = db.scalars(select(GeneratedAsset).where(GeneratedAsset.user_id == user.id).order_by(GeneratedAsset.created_at.desc()).limit(limit).offset(offset)).all()
    return Page(items=[GeneratedAssetOut.model_validate(r) for r in rows], total=total or 0, limit=limit, offset=offset)


@router.patch("/assets/{asset_id}", response_model=GeneratedAssetOut, dependencies=[Depends(require_csrf)])
def update_asset(asset_id: str, payload: AssetUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> GeneratedAssetOut:
    asset = db.get(GeneratedAsset, asset_id)
    if not asset or asset.user_id != user.id:
        raise NotFoundError("Asset not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    return GeneratedAssetOut.model_validate(asset)
