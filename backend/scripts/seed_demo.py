"""Seed a fully-populated demo account from a real resume PDF.

Usage (from the ``backend`` directory):

    .\\.venv\\Scripts\\python.exe scripts\\seed_demo.py
    .\\.venv\\Scripts\\python.exe scripts\\seed_demo.py --email demo@resumo.app --password demo1234

It creates (or resets) a single demo user and drives the *real* application
through every major feature — upload/parse, quality analysis, job description
matching, discovery, saved jobs, career roadmaps with milestones, project plans
with evidence and generated assets, resume tailoring, a published portfolio,
the application tracker, the profile and company research — so an evaluator can
log in and see every screen populated.

The script talks to the app exactly like the browser does (cookies + CSRF) via
FastAPI's TestClient, using the same database the dev server uses. It uses the
deterministic (non-AI) paths so it is fast and reproducible offline.
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    AnalysisFinding,
    AnalysisRun,
    Application,
    AuditEvent,
    BackgroundJob,
    CompanyCitation,
    CompanyResearch,
    ConsentRecord,
    GeneratedAsset,
    JobDescription,
    KeywordEvidence,
    LearningResource,
    MatchReport,
    PortfolioPage,
    Profile,
    ProjectEvidence,
    ProjectPlan,
    Resume,
    ResumeSection,
    ResumeVersion,
    Roadmap,
    RoadmapMilestone,
    SavedJob,
    SkillProfile,
    TailorSuggestion,
    UploadedFile,
    User,
)

DEFAULT_RESUME = REPO_ROOT / "Vicky_Resume_.pdf"

JOB_BACKEND = (
    "Job Title: Backend Engineering Intern\n"
    "Company: Acme Systems\n"
    "Location: Bengaluru (Hybrid)\n"
    "Requirements:\n"
    "Required: Python, Flask, REST APIs, MongoDB, SQL, Git, unit testing.\n"
    "Preferred: FastAPI, Docker, machine learning, scikit-learn, JavaScript.\n"
    "Responsibilities:\n"
    "Build and maintain REST APIs using Python and Flask.\n"
    "Develop data pipelines, write unit tests, and review code.\n"
    "Bachelor's degree in Computer Science or a related field.\n"
)
JOB_ML = (
    "Job Title: Machine Learning Intern\n"
    "Company: NeuraLabs\n"
    "Location: Remote\n"
    "Requirements:\n"
    "Required: Python, NumPy, Pandas, scikit-learn, machine learning fundamentals.\n"
    "Preferred: PyTorch, deep learning, data visualisation, Docker.\n"
    "Responsibilities:\n"
    "Build datasets, train and evaluate models, document reproducible experiments.\n"
)
JOB_DATA = (
    "Job Title: Data Analyst (Graduate)\n"
    "Company: QuantMetrics\n"
    "Location: Pune\n"
    "Requirements:\n"
    "Required: SQL, Python, Pandas, data visualisation, Excel, statistics.\n"
    "Preferred: Tableau, Power BI, A/B testing, dashboarding.\n"
)

SUMMARY = (
    "Final-year Computer Engineering student focused on AI/ML and backend development. "
    "Built and deployed four full-stack projects using Python, Flask, and machine-learning "
    "models, and served as an incoming TIH-IoT CHANAKYA Fellow. Seeking an internship where "
    "I can turn messy data into reliable, well-tested systems."
)
HEADLINE = "AI/ML & Backend Engineer - Final-year B.E. (Computer Engineering)"


# --------------------------------------------------------------------------------------
# Reset
# --------------------------------------------------------------------------------------
def _reset_user(db: Session, email: str) -> bool:
    """Remove an existing demo user and all rows that belong to them. Returns True if found."""
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user:
        return False
    uid = user.id

    resume_ids = select(Resume.id).where(Resume.user_id == uid)
    version_ids = select(ResumeVersion.id).where(ResumeVersion.resume_id.in_(resume_ids))
    analysis_ids = select(AnalysisRun.id).where(AnalysisRun.user_id == uid)
    match_ids = select(MatchReport.id).where(MatchReport.user_id == uid)
    roadmap_ids = select(Roadmap.id).where(Roadmap.user_id == uid)
    milestone_ids = select(RoadmapMilestone.id).where(RoadmapMilestone.roadmap_id.in_(roadmap_ids))
    research_ids = select(CompanyResearch.id).where(CompanyResearch.user_id == uid)

    # children first (FK-safe)
    db.execute(delete(AnalysisFinding).where(AnalysisFinding.run_id.in_(analysis_ids)))
    db.execute(delete(KeywordEvidence).where(KeywordEvidence.match_id.in_(match_ids)))
    db.execute(delete(LearningResource).where(LearningResource.milestone_id.in_(milestone_ids)))
    db.execute(delete(RoadmapMilestone).where(RoadmapMilestone.roadmap_id.in_(roadmap_ids)))
    db.execute(delete(CompanyCitation).where(CompanyCitation.research_id.in_(research_ids)))
    db.execute(delete(ResumeSection).where(ResumeSection.version_id.in_(version_ids)))
    db.execute(delete(ResumeVersion).where(ResumeVersion.resume_id.in_(resume_ids)))

    for model in (
        AnalysisRun, MatchReport, TailorSuggestion, SavedJob, Application,
        ProjectEvidence, GeneratedAsset, PortfolioPage, Roadmap,
        ProjectPlan, JobDescription, Resume, UploadedFile, SkillProfile,
        CompanyResearch, Profile, ConsentRecord, AuditEvent, BackgroundJob,
    ):
        db.execute(delete(model).where(model.user_id == uid))
    db.execute(delete(User).where(User.id == uid))
    db.commit()
    return True


def _seed_company_research(db: Session, user_id: str) -> None:
    research = CompanyResearch(
        user_id=user_id,
        company="Acme Systems (sample)",
        target_role="Backend Engineering Intern",
        summary=(
            "Illustrative sample record for the local demo. In production this is assembled "
            "only from public sources you provide (careers/engineering pages) and never as a "
            "claim about individuals."
        ),
        themes=["python", "apis", "reliability", "testing", "observability"],
        patterns=[
            "Engineering writing emphasises Python services, automated testing and observability.",
            "Individual examples are only shown when published publicly and appropriately.",
        ],
        confidence="inference",
    )
    db.add(research)
    db.flush()
    db.add(
        CompanyCitation(
            research_id=research.id,
            label="Sample engineering blog (demo data)",
            url="https://example.com/sample-labs/engineering",
            source_type="public",
            retrieved_at=None,
            excerpt="Sample citation for the offline demo — no live fetch was performed.",
        )
    )
    db.commit()


# --------------------------------------------------------------------------------------
# Seed
# --------------------------------------------------------------------------------------
def seed(email: str, password: str, full_name: str, resume_path: Path) -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app

    if not resume_path.exists():
        raise SystemExit(f"Resume not found: {resume_path}")

    app = create_app()
    with TestClient(app) as client:
        # reset any previous demo data
        with SessionLocal() as db:
            existed = _reset_user(db, email)
        if existed:
            print("- reset previous demo data")

        # ---- auth -------------------------------------------------------------
        client.get("/api/v1/auth/csrf")
        r = client.post("/api/v1/auth/signup", json={"email": email, "password": password, "full_name": full_name})
        if r.status_code != 200:
            raise SystemExit(f"signup failed: {r.status_code} {r.text}")
        body = r.json()
        headers = {"X-CSRF-Token": body["csrf_token"]}
        user_id = body["user"]["id"]
        print(f"- account: {email} (password: {password})")

        # ---- resume upload + enrich ------------------------------------------
        data = resume_path.read_bytes()
        up = client.post(
            "/api/v1/resumes/upload",
            files={"file": (resume_path.name, io.BytesIO(data), "application/pdf")},
            headers=headers,
        )
        if up.status_code != 201:
            raise SystemExit(f"upload failed: {up.status_code} {up.text}")
        up_body = up.json()
        resume_id = up_body["resume_id"]
        content = up_body["content"]
        content["contact"]["headline"] = HEADLINE
        content["contact"]["location"] = content["contact"].get("location") or "Mumbai, India"
        content["summary"] = SUMMARY
        client.patch(f"/api/v1/resumes/{resume_id}", json={"title": "Vicky Dsilva — Master Resume", "content": content}, headers=headers)
        print(f"- resume parsed ({up_body['detected_format']}, confidence {up_body['parse_confidence']})")

        # ---- quality analysis -------------------------------------------------
        client.post(f"/api/v1/resumes/{resume_id}/analyze", json={"use_ai": False, "target_role": "Backend Intern"}, headers=headers)

        # ---- job descriptions + matches --------------------------------------
        jobs = {}
        # Strongest match last so the dashboard's "latest match" is the best fit.
        for key, (title, company, text) in {
            "data": ("Data Analyst (Graduate)", "QuantMetrics", JOB_DATA),
            "ml": ("Machine Learning Intern", "NeuraLabs", JOB_ML),
            "backend": ("Backend Engineering Intern", "Acme Systems", JOB_BACKEND),
        }.items():
            jr = client.post("/api/v1/jobs", json={"title": title, "company": company, "raw_text": text}, headers=headers)
            jid = jr.json()["id"]
            mr = client.post("/api/v1/jobs/match", json={"job_id": jid, "resume_id": resume_id}, headers=headers).json()
            jobs[key] = {"id": jid, "match": mr["id"], "company": company, "title": title, "text": text, "score": mr["overall_score"]}
        for key, job in jobs.items():
            print(f"  - match {job['score']:>5}/100  {job['title']} @ {job['company']}")
        print(f"- {len(jobs)} job descriptions matched")

        # ---- discovery + saved jobs ------------------------------------------
        listings = client.get("/api/v1/listings", headers=headers).json()["items"]
        client.get("/api/v1/recommendations", headers=headers)
        client.post("/api/v1/saved-jobs", json={"title": jobs["backend"]["title"], "company": jobs["backend"]["company"], "job_id": jobs["backend"]["id"]}, headers=headers)
        if listings:
            client.post("/api/v1/saved-jobs", json={"title": listings[0]["title"], "company": listings[0]["company"], "listing_id": listings[0]["id"], "note": "Shortlisted from recommendations."}, headers=headers)
        if len(listings) > 1:
            client.post("/api/v1/saved-jobs", json={"title": listings[1]["title"], "company": listings[1]["company"], "listing_id": listings[1]["id"]}, headers=headers)

        # ---- roadmaps + milestones -------------------------------------------
        rm_backend = client.post("/api/v1/roadmaps", json={"target_role": "Backend Engineering Intern", "job_id": jobs["backend"]["id"], "resume_id": resume_id}, headers=headers).json()
        rm_ml = client.post("/api/v1/roadmaps", json={"target_role": "Machine Learning Intern", "job_id": jobs["ml"]["id"], "resume_id": resume_id}, headers=headers).json()
        milestones = rm_backend["milestones"]
        if milestones:
            client.patch(f"/api/v1/milestones/{milestones[0]['id']}", json={"status": "done", "notes": "Completed the official tutorial and shipped a small demo.", "evidence_url": "https://github.com/vickydsilva"}, headers=headers)
        if len(milestones) > 1:
            client.patch(f"/api/v1/milestones/{milestones[1]['id']}", json={"status": "in_progress", "notes": "Working through this now."}, headers=headers)
        print(f"- 2 roadmaps ({len(rm_backend['milestones'])} + {len(rm_ml['milestones'])} milestones)")

        # ---- project plans + evidence + assets -------------------------------
        p1 = client.post("/api/v1/projects", json={"title": "Production-grade REST API", "roadmap_id": rm_backend["id"]}, headers=headers).json()
        p2 = client.post("/api/v1/projects", json={"title": "ML model evaluation harness", "roadmap_id": rm_ml["id"]}, headers=headers).json()
        ev1 = client.post(
            f"/api/v1/projects/{p1['id']}/evidence",
            json={
                "title": "Production-grade REST API",
                "problem": "Needed a reliable, documented API for a student project.",
                "contribution": "Designed the schema, built the endpoints in Flask, and wrote unit tests.",
                "stack": ["Python", "Flask", "SQLite", "pytest"],
                "architecture": "Layered app: routes -> services -> repository.",
                "tests": "pytest suite covering the happy path and error cases.",
                "outcomes": "Stable local deployment used by classmates.",
                "repo_url": "https://github.com/vickydsilva",
            },
            headers=headers,
        ).json()
        ev2 = client.post(
            f"/api/v1/projects/{p2['id']}/evidence",
            json={
                "title": "ML model evaluation harness",
                "problem": "Comparing models was manual and error-prone.",
                "contribution": "Built a reproducible harness that trains and scores multiple models.",
                "stack": ["Python", "scikit-learn", "Pandas"],
                "outcomes": "One command reproduces every result.",
                "repo_url": "https://github.com/vickydsilva",
            },
            headers=headers,
        ).json()
        for kind, ref in [
            ("readme", {"project_evidence_id": ev1["id"]}),
            ("case_study", {"project_evidence_id": ev1["id"]}),
            ("project_summary", {"project_evidence_id": ev2["id"]}),
            ("bio", {"resume_id": resume_id, "job_id": jobs["backend"]["id"]}),
            ("cover_letter", {"resume_id": resume_id, "job_id": jobs["backend"]["id"]}),
            ("linkedin", {"resume_id": resume_id, "job_id": jobs["backend"]["id"]}),
            ("outreach", {"resume_id": resume_id, "job_id": jobs["ml"]["id"]}),
        ]:
            client.post("/api/v1/assets/generate", json={"kind": kind, "use_ai": False, **ref}, headers=headers)
        print("- 2 project plans, 2 evidence entries, 7 generated assets")

        # ---- tailoring (recommendation edits) --------------------------------
        # Inject two weak openers so the deterministic rewriter has something to improve.
        edited = dict(content)
        edited["experience"] = [dict(e) for e in content["experience"]]
        if edited["experience"] and edited["experience"][0]["bullets"]:
            b = list(edited["experience"][0]["bullets"])
            b[0] = "Worked on backend services for a student project."
            edited["experience"][0]["bullets"] = b
        edited["projects"] = [dict(p) for p in content["projects"]]
        if edited["projects"]:
            pb = list(edited["projects"][0]["bullets"]) or [""]
            pb[0] = "Helped with deploying the application to the cloud."
            edited["projects"][0]["bullets"] = pb
        client.patch(f"/api/v1/resumes/{resume_id}", json={"content": edited}, headers=headers)
        sugg = client.post("/api/v1/tailor/suggestions", json={"resume_id": resume_id, "job_id": jobs["backend"]["id"], "use_ai": False}, headers=headers).json()
        if sugg:
            # accept the first, leave the rest pending so both states are visible
            client.post("/api/v1/tailor/apply", json={"suggestion_ids": [sugg[0]["id"]], "accept": True}, headers=headers)
        print(f"- {len(sugg)} tailoring suggestions ({1 if sugg else 0} accepted, {max(0, len(sugg) - 1)} pending)")

        # ---- portfolio --------------------------------------------------------
        page = client.post("/api/v1/portfolio", headers=headers).json()
        project_ids = [p["name"] for p in content["projects"]]
        client.patch(
            f"/api/v1/portfolio/{page['id']}",
            json={
                "title": "Vicky Dsilva — Portfolio",
                "published": True,
                "settings": {"show_email": True, "show_phone": False, "show_links": True},
                "content": {
                    "bio": SUMMARY,
                    "headline": HEADLINE,
                    "projects": project_ids,
                    "links": [
                        {"label": "GitHub", "url": "https://github.com/vickydsilva"},
                        {"label": "LinkedIn", "url": "https://linkedin.com/in/vickydsilva"},
                    ],
                },
            },
            headers=headers,
        )
        print(f"- portfolio published at /p/{page['slug']}")

        # ---- applications tracker --------------------------------------------
        for title, company, status in [
            ("Backend Engineering Intern", "Acme Systems", "applied"),
            ("Machine Learning Intern", "NeuraLabs", "interview"),
            ("Data Analyst (Graduate)", "QuantMetrics", "saved"),
            ("Full-Stack Developer", "Sample Labs", "offer"),
            ("Frontend Developer", "Sample Labs", "rejected"),
        ]:
            ar = client.post(
                "/api/v1/applications",
                json={"company": company, "role": title, "status": status, "resume_id": resume_id},
                headers=headers,
            ).json()
            if status != "saved":
                client.patch(f"/api/v1/applications/{ar['id']}", json={"status": status}, headers=headers)
        print("- 5 applications across the pipeline")

        # ---- profile ----------------------------------------------------------
        client.patch(
            "/api/v1/profile",
            json={
                "headline": HEADLINE,
                "degree": "B.E. Computer Engineering",
                "institution": "Fr. Conceicao Rodrigues College of Engineering",
                "graduation_year": 2026,
                "target_roles": ["Backend Intern", "Machine Learning Intern", "Data Analyst"],
                "target_industries": ["Software", "Artificial Intelligence", "FinTech"],
                "target_companies": ["Acme Systems", "NeuraLabs", "QuantMetrics"],
                "preferred_locations": ["Mumbai", "Bengaluru", "Remote"],
                "work_arrangement": "any",
                "opportunity_type": "internship",
                "availability": "Immediately, full-time for 6 months",
                "skills": ["Python", "Flask", "scikit-learn", "Pandas", "SQL", "Git"],
                "coursework": ["Data Structures", "Machine Learning", "Databases", "Operating Systems"],
                "onboarding_completed": True,
            },
            headers=headers,
        )

        # ---- company research (sample, offline) ------------------------------
        with SessionLocal() as db:
            _seed_company_research(db, user_id)

        # ---- verify dashboard ------------------------------------------------
        dash = client.get("/api/v1/dashboard", headers=headers).json()
        print(
            "- dashboard: "
            f"{dash['resume_count']} resume(s), {dash['applications']} applications, "
            f"{dash['active_projects']} projects, quality {dash.get('latest_quality', {}) and dash['latest_quality']['score']}, "
            f"match {dash.get('latest_match', {}) and dash['latest_match']['score']}"
        )

    print("\nDemo account ready. Log in with:")
    print(f"  email:    {email}")
    print(f"  password: {password}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a fully-populated Resumo demo account.")
    parser.add_argument("--email", default="demo@resumo.app")
    parser.add_argument("--password", default="demo1234")
    parser.add_argument("--name", default="Vicky Dsilva")
    parser.add_argument("--resume", type=Path, default=DEFAULT_RESUME)
    args = parser.parse_args()
    seed(args.email, args.password, args.name, args.resume)


if __name__ == "__main__":
    main()
