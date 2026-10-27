"""Unit tests for keyword extraction, matching, and the truth-preservation checker."""
from __future__ import annotations

from app.schemas.resume import ExperienceItem, ProjectItem, ResumeContent, SkillGroup
from app.services.ai.truth import verify_suggestion
from app.services.matching.engine import extract_keywords, match_resume, parse_job

JD = """
We are hiring a backend intern.
Required: Python, REST API design, SQL, Docker.
Preferred: FastAPI and unit testing.
Responsibilities: Build and test APIs, collaborate with engineers.
Bachelor's degree required.
"""


def test_extract_keywords_marks_required_and_preferred():
    keywords = extract_keywords(JD)
    by_name = {k["keyword"]: k["importance"] for k in keywords}
    assert by_name.get("python") == "required"
    assert by_name.get("docker") == "required"
    assert by_name.get("fastapi") in ("preferred", "required")


def test_parse_job_returns_structured_fields():
    parsed = parse_job(JD)
    assert "python" in parsed["required_skills"]
    assert parsed["seniority"] == "intern"
    assert parsed["responsibilities"]


def test_match_reports_found_and_missing():
    content = ResumeContent(
        experience=[ExperienceItem(company="Acme", role="Intern", bullets=["Built a REST API in Python."])],
        skills=[SkillGroup(category="Skills", items=["Python", "SQL"])],
    )
    keywords = extract_keywords(JD)
    result = match_resume(content, keywords)
    statuses = {e["keyword"]: e["status"] for e in result["evidence"]}
    assert statuses["python"] == "found"
    assert statuses["docker"] == "missing"
    assert 0 <= result["overall_score"] <= 100


def test_semantic_synonym_normalisation():
    content = ResumeContent(skills=[SkillGroup(category="Skills", items=["JS"])])
    keywords = [{"keyword": "javascript", "importance": "required", "category": "skill"}]
    result = match_resume(content, keywords)
    assert result["evidence"][0]["status"] in ("weak", "found")


def test_distinct_technologies_not_merged():
    content = ResumeContent(skills=[SkillGroup(category="Skills", items=["Java"])])
    keywords = [{"keyword": "javascript", "importance": "required", "category": "skill"}]
    result = match_resume(content, keywords)
    assert result["evidence"][0]["status"] == "missing"


def test_truth_checker_blocks_invented_metric():
    source = "Built an API for reports."
    verified, flags = verify_suggestion(source, "Built an API that increased revenue by 400%.", source)
    assert verified is False
    assert any("400" in f for f in flags)


def test_truth_checker_blocks_invented_technology():
    source = "Built a backend service in Python."
    verified, flags = verify_suggestion(source, "Built a Kubernetes deployment in Python.", source)
    assert verified is False
    assert any("kubernetes" in f.lower() for f in flags)


def test_truth_checker_allows_faithful_rewrite():
    source = "Responsible for writing tests for the billing module."
    verified, flags = verify_suggestion(source, "Wrote and maintained tests for the billing module.", source)
    assert verified is True
    assert flags == []
