"""Job, matching, discovery, saved-jobs, and application schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    company: str | None = None
    location: str | None = None
    source_url: str | None = None
    raw_text: str = Field(min_length=20)
    opportunity_type: str | None = None


class ParsedJob(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    experience_years: str | None = None
    domain: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    terminology: list[str] = Field(default_factory=list)
    seniority: str | None = None


class JobOut(BaseModel):
    id: str
    title: str
    company: str | None
    location: str | None
    source_url: str | None
    opportunity_type: str | None
    seniority: str | None
    parsed: dict
    raw_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class KeywordOut(BaseModel):
    id: str
    keyword: str
    importance: str
    category: str
    status: str
    evidence_location: str | None
    evidence_excerpt: str | None
    recommended_action: str | None

    model_config = {"from_attributes": True}


class MatchRequest(BaseModel):
    job_id: str
    resume_id: str
    version_id: str | None = None
    use_ai: bool = False


class MatchOut(BaseModel):
    id: str
    job_id: str
    resume_id: str
    version_id: str
    overall_score: float | None
    coverage: float | None
    breakdown: dict
    methodology: str | None
    ai_used: bool
    keywords: list[KeywordOut]
    created_at: datetime


class JobListingOut(BaseModel):
    id: str
    title: str
    company: str
    location: str | None
    work_arrangement: str | None
    opportunity_type: str | None
    experience_level: str | None
    skills: list
    source: str
    source_url: str | None
    status: str
    is_sample: bool
    posted_at: datetime | None
    last_verified_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobRecommendation(BaseModel):
    listing: JobListingOut
    match_score: float
    reasons: list[str]
    improvement: list[str]


class SavedJobCreate(BaseModel):
    title: str
    company: str | None = None
    source_url: str | None = None
    job_id: str | None = None
    listing_id: str | None = None
    note: str | None = None


class SavedJobOut(BaseModel):
    id: str
    title: str
    company: str | None
    source_url: str | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    company: str
    role: str
    status: str = "saved"
    job_url: str | None = None
    source: str | None = None
    resume_id: str | None = None
    cover_letter: str | None = None
    contact_notes: str | None = None
    interview_notes: str | None = None
    match_id: str | None = None
    roadmap_id: str | None = None


class ApplicationUpdate(BaseModel):
    company: str | None = None
    role: str | None = None
    status: str | None = None
    job_url: str | None = None
    source: str | None = None
    resume_id: str | None = None
    cover_letter: str | None = None
    contact_notes: str | None = None
    interview_notes: str | None = None
    match_id: str | None = None
    roadmap_id: str | None = None
    applied_at: datetime | None = None
    deadline_at: datetime | None = None


class ApplicationOut(BaseModel):
    id: str
    company: str
    role: str
    status: str
    job_url: str | None
    source: str | None
    resume_id: str | None
    cover_letter: str | None
    contact_notes: str | None
    interview_notes: str | None
    match_id: str | None
    roadmap_id: str | None
    saved_at: datetime | None
    applied_at: datetime | None
    deadline_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
