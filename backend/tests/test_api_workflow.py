"""End-to-end workflow tests across the API."""
from __future__ import annotations

import io

SAMPLE = b"""Asha Rao
asha.rao@example.com | +91 90000 00000 | Bengaluru
github.com/asha

Summary
Backend-focused computer science student.

Experience
Software Intern - Acme
May 2025 - Jul 2025
- Built a REST API in Python reducing latency by 30%.

Projects
Resumo - FastAPI, React
- Implemented a parser registry supporting 10 formats.

Education
IIT Example - B.Tech CSE
2022 - 2026

Skills
Languages: Python, SQL, Docker, REST
"""


def _upload(client, headers):
    return client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(SAMPLE), "text/plain")},
        headers=headers,
    )


def test_full_resume_workflow(client, auth):
    headers, _ = auth("wf@example.com")

    up = _upload(client, headers)
    assert up.status_code == 201, up.text
    body = up.json()
    resume_id = body["resume_id"]
    assert body["detected_format"] == "txt"
    assert body["content"]["contact"]["email"] == "asha.rao@example.com"

    # edit the structured content
    body["content"]["summary"] = "Backend-focused CS student building reliable APIs."
    patched = client.patch(f"/api/v1/resumes/{resume_id}", json={"content": body["content"]}, headers=headers)
    assert patched.status_code == 200

    # quality analysis
    analysis = client.post(f"/api/v1/resumes/{resume_id}/analyze", json={"use_ai": False}, headers=headers)
    assert analysis.status_code == 200
    assert analysis.json()["overall_score"] is not None
    assert analysis.json()["methodology"]

    # duplicate + version history
    dup = client.post(f"/api/v1/resumes/{resume_id}/duplicate", headers=headers)
    assert dup.status_code == 200
    versions = client.get(f"/api/v1/resumes/{resume_id}/versions", headers=headers)
    assert versions.status_code == 200 and len(versions.json()) >= 1

    # create JD + match
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Backend Intern",
              "raw_text": "Required: Python, SQL, REST, Docker. Preferred: FastAPI. Build and test APIs. Bachelor degree."},
        headers=headers,
    )
    assert job.status_code == 201
    job_id = job.json()["id"]
    match = client.post("/api/v1/jobs/match", json={"job_id": job_id, "resume_id": resume_id}, headers=headers)
    assert match.status_code == 201
    assert 0 <= match.json()["overall_score"] <= 100
    keyword_statuses = {k["keyword"]: k["status"] for k in match.json()["keywords"]}
    assert keyword_statuses.get("python") == "found"

    # roadmap
    roadmap = client.post(
        "/api/v1/roadmaps",
        json={"target_role": "Backend Intern", "job_id": job_id, "resume_id": resume_id},
        headers=headers,
    )
    assert roadmap.status_code == 201
    assert len(roadmap.json()["milestones"]) >= 1

    # project
    project = client.post("/api/v1/projects", json={"title": "Backend API project", "roadmap_id": roadmap.json()["id"]}, headers=headers)
    assert project.status_code == 201
    project_id = project.json()["id"]

    # evidence + asset
    ev = client.post(f"/api/v1/projects/{project_id}/evidence",
                     json={"title": "My API", "contribution": "Built endpoints", "stack": ["FastAPI"]}, headers=headers)
    assert ev.status_code == 201
    asset = client.post("/api/v1/assets/generate", json={"kind": "readme", "project_evidence_id": ev.json()["id"], "use_ai": False}, headers=headers)
    assert asset.status_code == 201
    assert "Setup" in asset.json()["content"] or "Source facts" in asset.json()["content"]

    # application tracker
    app_row = client.post("/api/v1/applications", json={"company": "Acme", "role": "Backend Intern"}, headers=headers)
    assert app_row.status_code == 201
    updated = client.patch(f"/api/v1/applications/{app_row.json()['id']}", json={"status": "applied"}, headers=headers)
    assert updated.status_code == 200 and updated.json()["applied_at"] is not None

    # discovery + recommendations
    assert client.get("/api/v1/listings").json()["total"] >= 1
    recs = client.get("/api/v1/recommendations", headers=headers)
    assert recs.status_code == 200

    # dashboard reflects activity
    dash = client.get("/api/v1/dashboard", headers=headers).json()
    assert dash["resume_count"] >= 1
    assert dash["applications"] >= 1

    # settings/profile
    prof = client.patch("/api/v1/profile", json={"target_roles": ["Backend Intern"], "onboarding_completed": True}, headers=headers)
    assert prof.status_code == 200 and prof.json()["onboarding_completed"] is True


def test_export_all_formats(client, auth):
    headers, _ = auth("export@example.com")
    up = _upload(client, headers)
    resume_id = up.json()["resume_id"]
    for fmt, startswith in [("pdf", b"%PDF"), ("docx", b"PK"), ("txt", b"")]:
        resp = client.post(f"/api/v1/resumes/{resume_id}/export", json={"format": fmt}, headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.content[:4].startswith(startswith) if startswith else True
    latex = client.post(f"/api/v1/resumes/{resume_id}/export", json={"format": "latex"}, headers=headers)
    assert latex.status_code == 200
    assert b"\\documentclass" in latex.content
    assert b"jakegut" in latex.content.lower()


def test_upload_rejects_unsupported_format(client, auth):
    headers, _ = auth("badupload@example.com")
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")},
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unsupported_format"


def test_upload_rejects_oversized(client, auth, monkeypatch):
    headers, _ = auth("big@example.com")
    from app.core.config import settings

    monkeypatch.setattr(settings, "max_upload_mb", 0)
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("big.txt", io.BytesIO(b"a" * 2048), "text/plain")},
        headers=headers,
    )
    assert resp.status_code == 422


def test_tailor_truth_preservation(client, auth):
    headers, _ = auth("tailor@example.com")
    up = _upload(client, headers)
    resume_id = up.json()["resume_id"]
    job = client.post(
        "/api/v1/jobs",
        json={"title": "Backend Intern", "raw_text": "Required: Python, SQL, Docker. Build APIs."},
        headers=headers,
    )
    suggestions = client.post(
        "/api/v1/tailor/suggestions",
        json={"resume_id": resume_id, "job_id": job.json()["id"], "use_ai": False},
        headers=headers,
    )
    assert suggestions.status_code == 201
    # deterministic suggestions must all pass the truth check
    for s in suggestions.json():
        assert s["verified"] is True
