"""Career, roadmap, project, portfolio, tailoring, and research schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LearningResourceOut(BaseModel):
    id: str
    title: str
    url: str
    kind: str
    provider: str | None
    is_free: bool

    model_config = {"from_attributes": True}


class MilestoneOut(BaseModel):
    id: str
    position: int
    title: str
    kind: str
    week: int | None
    estimated_hours: int | None
    rationale: str | None
    source_requirement: str | None
    status: str
    evidence_url: str | None
    notes: str | None
    resources: list[LearningResourceOut] = []

    model_config = {"from_attributes": True}


class RoadmapOut(BaseModel):
    id: str
    target_role: str
    company: str | None
    readiness_score: float | None
    summary: str | None
    gap_report: dict
    ai_used: bool
    milestones: list[MilestoneOut]
    created_at: datetime

    model_config = {"from_attributes": True}


class RoadmapCreate(BaseModel):
    target_role: str
    company: str | None = None
    job_id: str | None = None
    resume_id: str | None = None
    use_ai: bool = False


class MilestoneUpdate(BaseModel):
    status: str | None = None
    evidence_url: str | None = None
    notes: str | None = None
    title: str | None = None
    estimated_hours: int | None = None


class ProjectPlanCreate(BaseModel):
    title: str
    problem: str | None = None
    roadmap_id: str | None = None
    use_ai: bool = False


class ProjectPlanOut(BaseModel):
    id: str
    roadmap_id: str | None
    title: str
    problem: str | None
    required_features: list
    optional_features: list
    suggested_stack: list
    milestones: list
    acceptance_criteria: list
    testing: str | None
    demonstrates: list
    evidence_to_publish: list
    resume_guidance: str | None
    stretch_goals: list
    status: str
    ai_used: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectEvidenceCreate(BaseModel):
    title: str
    problem: str | None = None
    contribution: str | None = None
    stack: list[str] = Field(default_factory=list)
    architecture: str | None = None
    tests: str | None = None
    outcomes: str | None = None
    repo_url: str | None = None
    demo_url: str | None = None
    docs_url: str | None = None
    interview_confident_areas: list[str] = Field(default_factory=list)


class ProjectEvidenceOut(ProjectEvidenceCreate):
    id: str
    project_plan_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioPageOut(BaseModel):
    id: str
    slug: str
    title: str
    published: bool
    settings: dict
    content: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class PortfolioUpdate(BaseModel):
    title: str | None = None
    published: bool | None = None
    settings: dict | None = None
    content: dict | None = None


class AssetGenerateRequest(BaseModel):
    kind: str  # readme|case_study|bio|cover_letter|linkedin|outreach|project_summary|presentation
    project_plan_id: str | None = None
    project_evidence_id: str | None = None
    resume_id: str | None = None
    job_id: str | None = None
    title: str | None = None
    use_ai: bool = True


class GeneratedAssetOut(BaseModel):
    id: str
    kind: str
    title: str
    content: str
    ai_used: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class TailorRequest(BaseModel):
    resume_id: str
    version_id: str | None = None
    job_id: str
    use_ai: bool = True


class TailorSuggestionOut(BaseModel):
    id: str
    original: str
    proposed: str
    rationale: str | None
    source_excerpt: str | None
    status: str
    verified: bool
    flags: list
    ai_used: bool

    model_config = {"from_attributes": True}


class TailorApplyRequest(BaseModel):
    suggestion_ids: list[str]
    accept: bool = True


class CompanyResearchRequest(BaseModel):
    company: str
    target_role: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    use_ai: bool = False


class CompanyCitationOut(BaseModel):
    id: str
    label: str
    url: str
    source_type: str
    retrieved_at: str | None
    excerpt: str | None

    model_config = {"from_attributes": True}


class CompanyResearchOut(BaseModel):
    id: str
    company: str
    target_role: str | None
    summary: str | None
    themes: list
    patterns: list
    confidence: str
    citations: list[CompanyCitationOut]
    created_at: datetime

    model_config = {"from_attributes": True}
