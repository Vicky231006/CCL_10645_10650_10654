"""Structured resume model and resume-related API schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LinkItem(BaseModel):
    label: str = ""
    url: str = ""


class ExperienceItem(BaseModel):
    company: str = ""
    role: str = ""
    location: str = ""
    start: str = ""
    end: str = ""
    bullets: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str = ""
    degree: str = ""
    location: str = ""
    start: str = ""
    end: str = ""
    details: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str = ""
    tech: list[str] = Field(default_factory=list)
    link: str = ""
    bullets: list[str] = Field(default_factory=list)


class SkillGroup(BaseModel):
    category: str = "Skills"
    items: list[str] = Field(default_factory=list)


class ResumeContact(BaseModel):
    name: str = ""
    headline: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    links: list[LinkItem] = Field(default_factory=list)


class ResumeContent(BaseModel):
    """The single editable internal representation for every resume."""

    contact: ResumeContact = Field(default_factory=ResumeContact)
    summary: str = ""
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    skills: list[SkillGroup] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    section_order: list[str] = Field(
        default_factory=lambda: ["summary", "experience", "projects", "education", "skills", "certifications", "achievements"]
    )
    section_visibility: dict[str, bool] = Field(default_factory=dict)

    def all_text(self) -> str:
        """Flatten to searchable text for keyword analysis."""
        parts: list[str] = [self.summary]
        for e in self.experience:
            parts += [e.company, e.role, *e.bullets]
        for ed in self.education:
            parts += [ed.institution, ed.degree, *ed.details]
        for p in self.projects:
            parts += [p.name, *p.tech, *p.bullets]
        for s in self.skills:
            parts += s.items
        parts += self.certifications + self.achievements
        return "\n".join([p for p in parts if p])


# ---- API schemas ----

class ResumeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    page_size: str = "A4"
    content: ResumeContent | None = None


class ResumeUpdate(BaseModel):
    title: str | None = None
    page_size: str | None = None
    content: ResumeContent | None = None
    label: str | None = None
    create_version: bool = False


class ResumeVersionOut(BaseModel):
    id: str
    version_number: int
    label: str
    is_primary: bool
    source_format: str | None
    parse_confidence: float | None
    content: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeOut(BaseModel):
    id: str
    title: str
    origin: str
    template: str
    page_size: str
    created_at: datetime
    updated_at: datetime
    latest_version: ResumeVersionOut | None = None

    model_config = {"from_attributes": True}


class UploadOut(BaseModel):
    resume_id: str
    version_id: str
    detected_format: str
    parse_confidence: float
    warnings: list[str]
    content: ResumeContent
    job_id: str | None = None


class FindingOut(BaseModel):
    id: str
    category: str
    severity: str
    source: str
    title: str
    excerpt: str | None
    explanation: str | None
    suggestion: str | None
    location: str | None

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    id: str
    resume_id: str
    version_id: str
    overall_score: float | None
    category_scores: dict
    methodology: str | None
    ai_used: bool
    ai_commentary: str | None
    findings: list[FindingOut]
    created_at: datetime


class AnalyzeRequest(BaseModel):
    use_ai: bool = False
    target_role: str | None = None


class ExportRequest(BaseModel):
    format: str = "pdf"  # pdf|docx|latex|txt
    version_id: str | None = None
    page_size: str | None = None
