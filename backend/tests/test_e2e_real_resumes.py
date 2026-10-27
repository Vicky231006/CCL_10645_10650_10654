"""End-to-end product tests against the two real demo resumes.

These exercise the full product surface (upload/parse, quality analysis, job
matching, discovery, saved jobs, roadmaps, projects, assets, tailoring,
portfolio, applications, profile and every export format) using the demo PDFs
that live at the repository root. The tests skip gracefully when the demo files
are absent so the suite stays portable.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

import pytest

from app.services.parsers.registry import parse_document

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_PDFS = [
    REPO_ROOT / "Ronak_Bhatia_Resume (3).pdf",
    REPO_ROOT / "Vicky_Resume_.pdf",
]

EXPECT = {
    "Ronak_Bhatia_Resume (3)": {
        "name": "Ronak Bhatia",
        "email": "bhatiaronak06@gmail.com",
        "min_projects": 3,
        "min_education": 2,
        "experience": 1,
        "expect_links": True,
    },
    "Vicky_Resume_": {
        "name": "Vicky Dsilva",
        "email": "vickydsilva2@gmail.com",
        "min_projects": 4,
        "min_education": 3,
        "experience": 1,
        "expect_links": True,
    },
}

JOB_TEXT = (
    "Job Title: Backend Engineering Intern\n"
    "Company: Acme Systems\n"
    "Requirements:\n"
    "Required: Python, Flask, REST, MongoDB, Git, SQL, unit testing.\n"
    "Preferred: FastAPI, Docker, machine learning, scikit-learn, JavaScript.\n"
    "Responsibilities:\n"
    "Build and maintain REST APIs using Python and Flask.\n"
    "Develop data pipelines, write unit tests, and review code.\n"
    "Bachelor's degree in Computer Science or a related field.\n"
)


def _email_for(stem: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", stem.lower())
    return f"e2e.{slug}@example.com"


def _upload(client, headers, pdf_path: Path):
    data = pdf_path.read_bytes()
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": (pdf_path.name, io.BytesIO(data), "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _reparse(text: str) -> str:
    """Re-parse an exported file's structured content into searchable text."""
    from app.services.parsers.structuring import structure_text

    content, _ = structure_text(text)
    return content.all_text()


@pytest.mark.parametrize("pdf_path", DEMO_PDFS, ids=lambda p: p.stem)
def test_demo_resume_full_workflow(client, auth, pdf_path: Path):
    if not pdf_path.exists():
        pytest.skip(f"demo resume not found: {pdf_path.name}")
    expect = EXPECT[pdf_path.stem]

    headers, user = auth(_email_for(pdf_path.stem))

    # ---- 1. Upload + parse ------------------------------------------------
    body = _upload(client, headers, pdf_path)
    assert body["detected_format"] == "pdf"
    assert body["parse_confidence"] >= 0.5
    content = body["content"]
    resume_id = body["resume_id"]

    assert content["contact"]["name"] == expect["name"]
    assert content["contact"]["email"].lower() == expect["email"]
    assert content["contact"]["phone"]
    assert len(content["projects"]) >= expect["min_projects"]
    assert len(content["education"]) >= expect["min_education"]
    assert len(content["experience"]) == expect["experience"]
    # multi-entry parsing: every education entry keeps its own dates
    assert all(e["institution"] for e in content["education"])
    assert content["education"][0]["start"] and content["education"][0]["end"]
    # every experience entry has a company and bullets
    for exp in content["experience"]:
        assert exp["company"] and exp["bullets"]
    # hyperlink annotations recovered into contact links
    if expect["expect_links"]:
        labels = {l["label"] for l in content["contact"]["links"]}
        assert "LinkedIn" in labels and "GitHub" in labels
    # no preamble leakage into summary
    assert content["summary"] == ""

    # list + get + versions
    listing = client.get("/api/v1/resumes", headers=headers)
    assert listing.status_code == 200 and listing.json()["total"] >= 1
    got = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
    assert got.status_code == 200 and got.json()["latest_version"]["content"]["contact"]["name"] == expect["name"]
    versions = client.get(f"/api/v1/resumes/{resume_id}/versions", headers=headers)
    assert versions.status_code == 200 and len(versions.json()) >= 1

    # ---- 2. Quality analysis (deterministic) ------------------------------
    analysis = client.post(
        f"/api/v1/resumes/{resume_id}/analyze",
        json={"use_ai": False, "target_role": "Backend Intern"},
        headers=headers,
    )
    assert analysis.status_code == 200, analysis.text
    a = analysis.json()
    assert a["overall_score"] is not None and 0 <= a["overall_score"] <= 10
    assert a["methodology"] and a["findings"]
    listed = client.get(f"/api/v1/resumes/{resume_id}/analyses", headers=headers)
    assert listed.status_code == 200 and len(listed.json()) >= 1

    # ---- 3. Duplicate + versioning ---------------------------------------
    dup = client.post(f"/api/v1/resumes/{resume_id}/duplicate", headers=headers)
    assert dup.status_code == 200 and dup.json()["id"] != resume_id
    client.delete(f"/api/v1/resumes/{dup.json()['id']}", headers=headers)

    # ---- 4. Job description + match --------------------------------------
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Backend Engineering Intern", "company": "Acme Systems", "raw_text": JOB_TEXT},
        headers=headers,
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]
    assert job.json()["parsed"]["required_skills"]

    match = client.post(
        "/api/v1/jobs/match",
        json={"job_id": job_id, "resume_id": resume_id},
        headers=headers,
    )
    assert match.status_code == 201, match.text
    m = match.json()
    assert 0 <= m["overall_score"] <= 100
    statuses = {k["keyword"]: k["status"] for k in m["keywords"]}
    assert statuses.get("python") == "found"
    assert m["breakdown"]["keywords_total"] == len(m["keywords"])
    assert any(k["status"] == "missing" for k in m["keywords"])
    assert client.get(f"/api/v1/matches/{m['id']}", headers=headers).status_code == 200
    assert client.get("/api/v1/matches", headers=headers).json()["total"] >= 1

    # ---- 5. Discovery, recommendations, saved jobs -----------------------
    listings = client.get("/api/v1/listings", headers=headers)
    assert listings.status_code == 200 and listings.json()["total"] >= 1
    recs = client.get("/api/v1/recommendations", headers=headers)
    assert recs.status_code == 200 and len(recs.json()) >= 1
    assert recs.json()[0]["listing"]["title"]
    saved = client.post(
        "/api/v1/saved-jobs",
        json={"title": "Backend Engineering Intern", "company": "Acme Systems", "job_id": job_id},
        headers=headers,
    )
    assert saved.status_code == 201
    saved_id = saved.json()["id"]
    assert len(client.get("/api/v1/saved-jobs", headers=headers).json()) >= 1

    # ---- 6. Roadmap + milestones -----------------------------------------
    roadmap = client.post(
        "/api/v1/roadmaps",
        json={"target_role": "Backend Engineering Intern", "job_id": job_id, "resume_id": resume_id},
        headers=headers,
    )
    assert roadmap.status_code == 201, roadmap.text
    r = roadmap.json()
    assert r["milestones"], "roadmap should produce milestones for the gaps"
    assert r["gap_report"]["missing_required"] is not None
    milestone_id = r["milestones"][0]["id"]
    updated = client.patch(
        f"/api/v1/milestones/{milestone_id}",
        json={"status": "done", "notes": "Completed the tutorial.", "evidence_url": "https://example.com/proof"},
        headers=headers,
    )
    assert updated.status_code == 200 and updated.json()["status"] == "done"
    assert client.get(f"/api/v1/roadmaps/{r['id']}", headers=headers).json()["milestones"][0]["status"] == "done"

    # ---- 7. Project plan + evidence + assets -----------------------------
    project = client.post(
        "/api/v1/projects",
        json={"title": "Backend API portfolio project", "roadmap_id": r["id"]},
        headers=headers,
    )
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]
    assert project.json()["required_features"] and project.json()["milestones"]
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers).status_code == 200
    assert client.get("/api/v1/projects", headers=headers).json()["total"] >= 1

    evidence = client.post(
        f"/api/v1/projects/{project_id}/evidence",
        json={
            "title": "Backend API",
            "problem": "Needed a reliable API.",
            "contribution": "Built the endpoints and tests.",
            "stack": ["Python", "Flask"],
            "outcomes": "Works end to end.",
        },
        headers=headers,
    )
    assert evidence.status_code == 201
    evidence_id = evidence.json()["id"]
    assert len(client.get(f"/api/v1/projects/{project_id}/evidence", headers=headers).json()) == 1

    readme = client.post(
        "/api/v1/assets/generate",
        json={"kind": "readme", "project_evidence_id": evidence_id, "use_ai": False},
        headers=headers,
    )
    assert readme.status_code == 201, readme.text
    assert "Setup" in readme.json()["content"] or "Source facts" in readme.json()["content"]
    bio = client.post(
        "/api/v1/assets/generate",
        json={"kind": "bio", "resume_id": resume_id, "job_id": job_id, "use_ai": False},
        headers=headers,
    )
    assert bio.status_code == 201
    asset_id = bio.json()["id"]
    assert client.get("/api/v1/assets", headers=headers).json()["total"] >= 2
    patched_asset = client.patch(f"/api/v1/assets/{asset_id}", json={"content": "Edited bio."}, headers=headers)
    assert patched_asset.status_code == 200 and patched_asset.json()["content"] == "Edited bio."

    # ---- 8. Tailoring: suggestions, verify, apply/edit -------------------
    # Inject a weak opener so the deterministic rewriter produces a suggestion.
    edited = dict(content)
    edited["experience"] = [dict(e) for e in content["experience"]]
    edited["experience"][0]["bullets"] = ["Responsible for building reliable services."] + edited["experience"][0]["bullets"][1:]
    up_edit = client.patch(f"/api/v1/resumes/{resume_id}", json={"content": edited}, headers=headers)
    assert up_edit.status_code == 200, up_edit.text

    suggestions = client.post(
        "/api/v1/tailor/suggestions",
        json={"resume_id": resume_id, "job_id": job_id, "use_ai": False},
        headers=headers,
    )
    assert suggestions.status_code == 201, suggestions.text
    sugg = suggestions.json()
    assert sugg, "a weak bullet should yield at least one suggestion"
    assert all(s["verified"] for s in sugg)
    applied = client.post(
        "/api/v1/tailor/apply",
        json={"suggestion_ids": [s["id"] for s in sugg], "accept": True},
        headers=headers,
    )
    assert applied.status_code == 200 and applied.json()["applied"] >= 1
    after = client.get(f"/api/v1/resumes/{resume_id}", headers=headers).json()
    bullets = after["latest_version"]["content"]["experience"][0]["bullets"]
    assert not any(b.lower().startswith("responsible for") for b in bullets)
    assert any(b.lower().startswith("building") for b in bullets)
    listed_sugg = client.get(f"/api/v1/tailor/suggestions?resume_id={resume_id}", headers=headers).json()
    assert any(s["status"] == "accepted" for s in listed_sugg)

    # ---- 9. Portfolio create / publish / public view ---------------------
    page = client.post("/api/v1/portfolio", headers=headers)
    assert page.status_code == 201, page.text
    page_id, slug = page.json()["id"], page.json()["slug"]
    assert client.get("/api/v1/portfolio/public/{0}".format(slug), headers=headers).status_code == 404
    published = client.patch(
        f"/api/v1/portfolio/{page_id}",
        json={"published": True, "title": "Demo Portfolio", "content": {"summary": "Hi"}},
        headers=headers,
    )
    assert published.status_code == 200 and published.json()["published"]
    public = client.get(f"/api/v1/portfolio/public/{slug}", headers=headers)
    assert public.status_code == 200 and public.json()["title"] == "Demo Portfolio"
    assert client.get("/api/v1/portfolio", headers=headers).status_code == 200

    # ---- 10. Applications tracker ----------------------------------------
    app_row = client.post(
        "/api/v1/applications",
        json={"company": "Acme Systems", "role": "Backend Intern", "resume_id": resume_id, "match_id": m["id"]},
        headers=headers,
    )
    assert app_row.status_code == 201
    app_id = app_row.json()["id"]
    moved = client.patch(f"/api/v1/applications/{app_id}", json={"status": "applied"}, headers=headers)
    assert moved.status_code == 200 and moved.json()["applied_at"]
    assert client.get("/api/v1/applications", headers=headers).json()["total"] >= 1
    assert client.get(f"/api/v1/applications/{app_id}", headers=headers).status_code == 200

    # ---- 11. Profile + dashboard -----------------------------------------
    prof = client.patch(
        "/api/v1/profile",
        json={"target_roles": ["Backend Intern"], "onboarding_completed": True},
        headers=headers,
    )
    assert prof.status_code == 200 and prof.json()["onboarding_completed"] is True
    dash = client.get("/api/v1/dashboard", headers=headers)
    assert dash.status_code == 200
    d = dash.json()
    assert d["resume_count"] >= 1 and d["applications"] >= 1
    assert d["latest_quality"] and d["latest_match"] and d["roadmap"]

    # ---- 12. Company research (SSRF-safe, no live network) ---------------
    bad = client.post(
        "/api/v1/company-research",
        json={"company": "Acme", "source_urls": ["http://10.0.0.1/private"]},
        headers=headers,
    )
    assert bad.status_code == 422
    assert client.get("/api/v1/company-research", headers=headers).status_code == 200

    # ---- 13. Export every format + round-trip ----------------------------
    for fmt, parser_fmt, sig, where in [
        ("pdf", "pdf", b"%PDF", "start"),
        ("docx", "docx", b"PK", "start"),
        ("txt", "txt", b"", None),
        ("latex", "tex", b"\\documentclass", "in"),
    ]:
        resp = client.post(
            f"/api/v1/resumes/{resume_id}/export",
            json={"format": fmt},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        if where == "start":
            assert resp.content.startswith(sig), f"{fmt} signature mismatch"
        elif where == "in":
            assert sig in resp.content, f"{fmt} signature mismatch"
        parsed = parse_document(parser_fmt, resp.content)
        assert expect["name"] in parsed.text, f"{fmt} export lost the name"
    assert client.post(
        f"/api/v1/resumes/{resume_id}/export", json={"format": "exe"}, headers=headers
    ).status_code == 422

    # cleanup saved job + application to exercise deletes
    assert client.delete(f"/api/v1/saved-jobs/{saved_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/applications/{app_id}", headers=headers).status_code == 204


@pytest.mark.parametrize("pdf_path", DEMO_PDFS, ids=lambda p: p.stem)
def test_demo_resume_edit_and_export_roundtrip(client, auth, pdf_path: Path):
    """Edits made in the resume editor survive every export format (format preservation)."""
    if not pdf_path.exists():
        pytest.skip(f"demo resume not found: {pdf_path.name}")

    headers, _ = auth(_email_for("roundtrip" + pdf_path.stem))
    body = _upload(client, headers, pdf_path)
    resume_id = body["resume_id"]
    content = body["content"]

    marker = "ResumoVerifyMarker42"
    edited = dict(content)
    edited["summary"] = f"Engineer who ships verified systems. {marker}"
    edited["experience"] = [dict(e) for e in content["experience"]]
    edited["experience"][0]["bullets"] = [f"Delivered the core platform. {marker}"] + list(
        edited["experience"][0]["bullets"][1:]
    )
    edited["certifications"] = list(content["certifications"]) + [f"Verified Certificate {marker}"]

    patched = client.patch(f"/api/v1/resumes/{resume_id}", json={"content": edited}, headers=headers)
    assert patched.status_code == 200, patched.text

    # the stored resume reflects the edits
    stored = client.get(f"/api/v1/resumes/{resume_id}", headers=headers).json()["latest_version"]["content"]
    assert marker in stored["summary"]
    assert marker in stored["experience"][0]["bullets"][0]
    assert marker in " ".join(stored["certifications"])

    # create a new version explicitly and confirm version history grows
    versioned = client.patch(
        f"/api/v1/resumes/{resume_id}",
        json={"content": edited, "create_version": True, "label": "Tailored"},
        headers=headers,
    )
    assert versioned.status_code == 200
    versions = client.get(f"/api/v1/resumes/{resume_id}/versions", headers=headers).json()
    assert len(versions) >= 2

    # every export format preserves the edited content
    formats = [("pdf", "pdf"), ("docx", "docx"), ("txt", "txt"), ("latex", "tex")]
    for requested, parser_fmt in formats:
        resp = client.post(f"/api/v1/resumes/{resume_id}/export", json={"format": requested}, headers=headers)
        assert resp.status_code == 200, resp.text
        parsed = parse_document(parser_fmt, resp.content)
        combined = parsed.text + "\n" + _reparse(parsed.text)
        assert marker in combined, f"{requested} export lost the edited marker"
        # structure also survives: at least one project word is still present
        tokens = [w for p in content["projects"] for w in re.findall(r"[A-Za-z][A-Za-z0-9.+]{3,}", p["name"])]
        assert any(t in combined for t in tokens), f"{requested} export lost project structure"
