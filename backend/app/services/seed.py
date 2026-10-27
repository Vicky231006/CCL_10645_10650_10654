"""Labelled sample data for local development and job discovery.

Everything created here is explicitly marked as sample data (`is_sample=True`) and is
NEVER presented as a live vacancy. Real integrations plug into the same adapter interface.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import JobListing

SAMPLE_LISTINGS: list[dict] = [
    {
        "title": "Software Engineering Intern (Backend)",
        "company": "Sample Labs",
        "location": "Bengaluru, India",
        "work_arrangement": "hybrid",
        "opportunity_type": "internship",
        "experience_level": "entry",
        "skills": ["python", "sql", "rest", "git", "docker"],
        "description": (
            "We are looking for a backend engineering intern. Required: strong Python, REST API design, "
            "SQL databases, and Git. Preferred: Docker, unit testing, cloud (AWS). You will build and test "
            "services, write documentation, and collaborate with senior engineers."
        ),
    },
    {
        "title": "Frontend Developer (React)",
        "company": "Sample Labs",
        "location": "Remote",
        "work_arrangement": "remote",
        "opportunity_type": "full_time",
        "experience_level": "entry",
        "skills": ["javascript", "typescript", "react", "html", "css", "git"],
        "description": (
            "Build accessible user interfaces with React and TypeScript. Required: JavaScript/TypeScript, "
            "React, HTML/CSS. Preferred: Tailwind, testing, accessibility. You will ship features and "
            "collaborate with designers."
        ),
    },
    {
        "title": "Machine Learning Intern",
        "company": "Sample Labs",
        "location": "Hyderabad, India",
        "work_arrangement": "onsite",
        "opportunity_type": "internship",
        "experience_level": "entry",
        "skills": ["python", "pytorch", "numpy", "pandas", "machine learning", "git"],
        "description": (
            "Machine learning internship focused on model training and evaluation. Required: Python, NumPy, "
            "Pandas, PyTorch, fundamentals of machine learning. Preferred: scikit-learn, data visualisation, "
            "reproducible experiments. You will build datasets, train models, and document results."
        ),
    },
    {
        "title": "Cloud/DevOps Engineer (Graduate)",
        "company": "Sample Labs",
        "location": "Pune, India",
        "work_arrangement": "hybrid",
        "opportunity_type": "full_time",
        "experience_level": "entry",
        "skills": ["aws", "docker", "kubernetes", "terraform", "linux", "ci/cd", "bash"],
        "description": (
            "Join our platform team. Required: Linux, AWS fundamentals, Docker, CI/CD. Preferred: Kubernetes, "
            "Terraform, monitoring. You will automate deployments and improve reliability."
        ),
    },
    {
        "title": "Full-Stack Developer",
        "company": "Sample Labs",
        "location": "Remote",
        "work_arrangement": "remote",
        "opportunity_type": "full_time",
        "experience_level": "junior",
        "skills": ["javascript", "react", "node.js", "postgresql", "rest", "docker"],
        "description": (
            "Full-stack role. Required: React, Node.js, SQL (PostgreSQL), REST APIs. Preferred: Docker, "
            "TypeScript, testing. You will own features end to end."
        ),
    },
]

SAMPLE_RESUME_TEXT = """Asha Rao
asha.rao@example.com | +91 90000 00000 | Bengaluru, India
github.com/asha-rao | linkedin.com/in/asha-rao

Summary
Final-year B.Tech Computer Science student. Backend-focused, comfortable with Python and APIs.

Education
Indian Institute of Technology, Example — B.Tech Computer Science
2022 - 2026

Experience
Software Engineering Intern — Acme Systems
May 2025 - Jul 2025
• Built a REST API in Python that reduced report generation time by 40%.
• Wrote unit tests and documentation for the billing module.

Projects
Resumo — FastAPI, React
• Implemented a parser registry supporting 10 resume formats.
• Designed a deterministic scoring engine with transparent rules.

Skills
Languages: Python, TypeScript, SQL
Frameworks: FastAPI, React
Tools: Git, Docker
"""


def seed_job_listings(db: Session) -> int:
    existing = db.scalar(select(JobListing).limit(1))
    if existing is not None:
        return 0
    now = datetime.now(timezone.utc)
    created = 0
    for item in SAMPLE_LISTINGS:
        db.add(
            JobListing(
                title=item["title"],
                company=item["company"],
                description=item["description"],
                skills=item["skills"],
                location=item["location"],
                work_arrangement=item["work_arrangement"],
                opportunity_type=item["opportunity_type"],
                experience_level=item["experience_level"],
                source="seed",
                source_url=None,
                status="unverified",
                is_sample=True,
                last_verified_at=now,
            )
        )
        created += 1
    db.commit()
    return created
