"""Skills, roadmaps, learning resources, project plans, portfolio, generated assets."""
from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class SkillProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "skill_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), default="skill")
    proficiency: Mapped[str | None] = mapped_column(String(40))  # learning|working|strong
    evidence: Mapped[str | None] = mapped_column(Text)


class Roadmap(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "roadmaps"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("job_descriptions.id", ondelete="SET NULL"))
    resume_id: Mapped[str | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    target_role: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str | None] = mapped_column(String(240))
    readiness_score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    gap_report: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)

    milestones: Mapped[list["RoadmapMilestone"]] = relationship(
        back_populates="roadmap", cascade="all, delete-orphan", order_by="RoadmapMilestone.position"
    )


class RoadmapMilestone(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "roadmap_milestones"

    roadmap_id: Mapped[str] = mapped_column(ForeignKey("roadmaps.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(default=0)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), default="skill")  # skill|project|experience|fundamentals
    week: Mapped[int | None] = mapped_column()
    estimated_hours: Mapped[int | None] = mapped_column()
    rationale: Mapped[str | None] = mapped_column(Text)
    source_requirement: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="todo")  # todo|in_progress|done
    evidence_url: Mapped[str | None] = mapped_column(String(1000))
    notes: Mapped[str | None] = mapped_column(Text)

    roadmap: Mapped[Roadmap] = relationship(back_populates="milestones")
    resources: Mapped[list["LearningResource"]] = relationship(
        back_populates="milestone", cascade="all, delete-orphan"
    )


class LearningResource(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "learning_resources"

    milestone_id: Mapped[str] = mapped_column(
        ForeignKey("roadmap_milestones.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    kind: Mapped[str] = mapped_column(String(40), default="docs")  # docs|course|tutorial|book
    provider: Mapped[str | None] = mapped_column(String(160))
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)

    milestone: Mapped[RoadmapMilestone] = relationship(back_populates="resources")


class ProjectPlan(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_plans"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    roadmap_id: Mapped[str | None] = mapped_column(ForeignKey("roadmaps.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    problem: Mapped[str | None] = mapped_column(Text)
    required_features: Mapped[list] = mapped_column(JSON, default=list)
    optional_features: Mapped[list] = mapped_column(JSON, default=list)
    suggested_stack: Mapped[list] = mapped_column(JSON, default=list)
    milestones: Mapped[list] = mapped_column(JSON, default=list)
    acceptance_criteria: Mapped[list] = mapped_column(JSON, default=list)
    testing: Mapped[str | None] = mapped_column(Text)
    demonstrates: Mapped[list] = mapped_column(JSON, default=list)
    evidence_to_publish: Mapped[list] = mapped_column(JSON, default=list)
    resume_guidance: Mapped[str | None] = mapped_column(Text)
    stretch_goals: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(24), default="planned")  # planned|building|done
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)


class ProjectEvidence(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "project_evidence"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_plan_id: Mapped[str | None] = mapped_column(ForeignKey("project_plans.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    problem: Mapped[str | None] = mapped_column(Text)
    contribution: Mapped[str | None] = mapped_column(Text)
    stack: Mapped[list] = mapped_column(JSON, default=list)
    architecture: Mapped[str | None] = mapped_column(Text)
    tests: Mapped[str | None] = mapped_column(Text)
    outcomes: Mapped[str | None] = mapped_column(Text)
    repo_url: Mapped[str | None] = mapped_column(String(1000))
    demo_url: Mapped[str | None] = mapped_column(String(1000))
    docs_url: Mapped[str | None] = mapped_column(String(1000))
    interview_confident_areas: Mapped[list] = mapped_column(JSON, default=list)


class PortfolioPage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "portfolio_pages"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)  # visibility toggles
    content: Mapped[dict] = mapped_column(JSON, default=dict)


class GeneratedAsset(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "generated_assets"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    project_plan_id: Mapped[str | None] = mapped_column(ForeignKey("project_plans.id", ondelete="SET NULL"))
    resume_id: Mapped[str | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(60), nullable=False)  # readme|case_study|bio|cover_letter|linkedin|outreach
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)


class TailorSuggestion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tailor_suggestions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("resume_versions.id", ondelete="CASCADE"))
    job_id: Mapped[str | None] = mapped_column(ForeignKey("job_descriptions.id", ondelete="SET NULL"))
    original: Mapped[str] = mapped_column(Text)
    proposed: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text)
    source_excerpt: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="pending")  # pending|accepted|rejected
    verified: Mapped[bool] = mapped_column(Boolean, default=True)  # passes truth check
    flags: Mapped[list] = mapped_column(JSON, default=list)
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)


class CompanyResearch(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "company_research"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company: Mapped[str] = mapped_column(String(240), nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(300))
    summary: Mapped[str | None] = mapped_column(Text)
    themes: Mapped[list] = mapped_column(JSON, default=list)
    patterns: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[str] = mapped_column(String(20), default="inference")  # verified | inference
    citations: Mapped[list["CompanyCitation"]] = relationship(
        back_populates="research", cascade="all, delete-orphan"
    )


class CompanyCitation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "company_citations"

    research_id: Mapped[str] = mapped_column(
        ForeignKey("company_research.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_type: Mapped[str] = mapped_column(String(60), default="public")
    retrieved_at: Mapped[str | None] = mapped_column(String(40))
    excerpt: Mapped[str | None] = mapped_column(Text)

    research: Mapped[CompanyResearch] = relationship(back_populates="citations")
