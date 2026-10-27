"""Profile / onboarding schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    company: str = ""
    role: str = ""
    location: str = ""
    start: str = ""
    end: str = ""
    bullets: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    tech: list[str] = Field(default_factory=list)
    link: str = ""


class ProfileUpdate(BaseModel):
    headline: str | None = None
    degree: str | None = None
    institution: str | None = None
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)
    academic_notes: str | None = None
    target_roles: list[str] | None = None
    target_industries: list[str] | None = None
    target_companies: list[str] | None = None
    preferred_locations: list[str] | None = None
    work_arrangement: str | None = None
    opportunity_type: str | None = None
    availability: str | None = None
    skills: list[str] | None = None
    coursework: list[str] | None = None
    experience: list[ExperienceEntry] | None = None
    projects: list[ProjectEntry] | None = None
    links: dict | None = None
    onboarding_completed: bool | None = None


class ProfileOut(BaseModel):
    id: str
    headline: str | None
    degree: str | None
    institution: str | None
    graduation_year: int | None
    academic_notes: str | None
    target_roles: list
    target_industries: list
    target_companies: list
    preferred_locations: list
    work_arrangement: str | None
    opportunity_type: str | None
    availability: str | None
    skills: list
    coursework: list
    experience: list
    projects: list
    links: dict
    onboarding_completed: bool
    updated_at: datetime

    model_config = {"from_attributes": True}
