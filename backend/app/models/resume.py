"""Resume documents, versions, sections, analysis runs and findings."""
from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class Resume(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    origin: Mapped[str] = mapped_column(String(40), default="upload")  # upload | builder | seed
    template: Mapped[str] = mapped_column(String(60), default="jakes")
    page_size: Mapped[str] = mapped_column(String(12), default="A4")  # A4 | LETTER
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeVersion.version_number"
    )


class ResumeVersion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resume_versions"

    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(default=1, nullable=False)
    label: Mapped[str] = mapped_column(String(160), default="Original")
    # Structured resume model (see app.schemas.resume.ResumeContent)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    source_format: Mapped[str | None] = mapped_column(String(20))
    parse_confidence: Mapped[float | None] = mapped_column(Float)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    resume: Mapped[Resume] = relationship(back_populates="versions")
    sections: Mapped[list["ResumeSection"]] = relationship(
        back_populates="version", cascade="all, delete-orphan", order_by="ResumeSection.position"
    )


class ResumeSection(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "resume_sections"

    version_id: Mapped[str] = mapped_column(ForeignKey("resume_versions.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(60), nullable=False)  # summary|experience|projects|education|skills|...
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    position: Mapped[int] = mapped_column(default=0)
    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, default=dict)

    version: Mapped[ResumeVersion] = relationship(back_populates="sections")


class UploadedFile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "uploaded_files"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[str | None] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(400), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(default=0)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[str | None] = mapped_column(String(64))
    detected_format: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(24), default="stored")  # stored|parsed|failed
    notes: Mapped[str | None] = mapped_column(Text)


class AnalysisRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "analysis_runs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("resume_versions.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40), default="quality")  # quality
    overall_score: Mapped[float | None] = mapped_column(Float)
    category_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    methodology: Mapped[str | None] = mapped_column(Text)
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_commentary: Mapped[str | None] = mapped_column(Text)

    findings: Mapped[list["AnalysisFinding"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class AnalysisFinding(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "analysis_findings"

    run_id: Mapped[str] = mapped_column(ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # critical|important|polish
    source: Mapped[str] = mapped_column(String(20), default="rule")  # rule | ai
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))

    run: Mapped[AnalysisRun] = relationship(back_populates="findings")
