"""Job descriptions, matches, keyword evidence, discovered listings, saved jobs, applications."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class JobDescription(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "job_descriptions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str | None] = mapped_column(String(240))
    location: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed: Mapped[dict] = mapped_column(JSON, default=dict)  # structured JD (skills etc.)
    seniority: Mapped[str | None] = mapped_column(String(60))
    opportunity_type: Mapped[str | None] = mapped_column(String(40))

    matches: Mapped[list["MatchReport"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class MatchReport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "match_reports"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("resume_versions.id", ondelete="CASCADE"), index=True)

    overall_score: Mapped[float | None] = mapped_column(Float)  # 0-100 alignment
    coverage: Mapped[float | None] = mapped_column(Float)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    methodology: Mapped[str | None] = mapped_column(Text)
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)

    keywords: Mapped[list["KeywordEvidence"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )
    job: Mapped[JobDescription] = relationship(back_populates="matches")


class KeywordEvidence(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "keyword_evidence"

    match_id: Mapped[str] = mapped_column(ForeignKey("match_reports.id", ondelete="CASCADE"), index=True)
    keyword: Mapped[str] = mapped_column(String(200), nullable=False)
    importance: Mapped[str] = mapped_column(String(20), nullable=False)  # required | preferred | bonus
    category: Mapped[str] = mapped_column(String(60), default="skill")
    status: Mapped[str] = mapped_column(String(24), nullable=False)  # found | weak | missing
    evidence_location: Mapped[str | None] = mapped_column(String(240))
    evidence_excerpt: Mapped[str | None] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)

    match: Mapped[MatchReport] = relationship(back_populates="keywords")


class JobListing(UUIDMixin, TimestampMixin, Base):
    """Normalised discovered listing. `is_sample` marks clearly-labelled seed data."""

    __tablename__ = "job_listings"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    location: Mapped[str | None] = mapped_column(String(200))
    work_arrangement: Mapped[str | None] = mapped_column(String(40))
    opportunity_type: Mapped[str | None] = mapped_column(String(40))
    experience_level: Mapped[str | None] = mapped_column(String(60))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(80), default="seed")
    source_url: Mapped[str | None] = mapped_column(String(1000))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), default="unverified")  # active | expired | unverified
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SavedJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "saved_jobs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("job_descriptions.id", ondelete="SET NULL"), index=True)
    listing_id: Mapped[str | None] = mapped_column(ForeignKey("job_listings.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str | None] = mapped_column(String(240))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    note: Mapped[str | None] = mapped_column(Text)


class Application(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "applications"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company: Mapped[str] = mapped_column(String(240), nullable=False)
    role: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="saved", index=True)
    # saved|applied|interview|offer|rejected|withdrawn
    job_url: Mapped[str | None] = mapped_column(String(1000))
    source: Mapped[str | None] = mapped_column(String(120))
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resume_id: Mapped[str | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    cover_letter: Mapped[str | None] = mapped_column(Text)
    contact_notes: Mapped[str | None] = mapped_column(Text)
    interview_notes: Mapped[str | None] = mapped_column(Text)
    match_id: Mapped[str | None] = mapped_column(ForeignKey("match_reports.id", ondelete="SET NULL"))
    roadmap_id: Mapped[str | None] = mapped_column(ForeignKey("roadmaps.id", ondelete="SET NULL"))
