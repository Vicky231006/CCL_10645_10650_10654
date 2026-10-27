"""Unit tests for the deterministic quality engine."""
from __future__ import annotations

from app.schemas.resume import (
    EducationItem,
    ExperienceItem,
    ProjectItem,
    ResumeContact,
    ResumeContent,
    SkillGroup,
)
from app.services.quality.engine import analyze_quality


def _good_resume() -> ResumeContent:
    return ResumeContent(
        contact=ResumeContact(name="Asha Rao", email="asha@example.com", phone="+91 90000 00000",
                              location="Bengaluru", links=[{"label": "GitHub", "url": "https://github.com/asha"}]),
        summary="Backend-focused computer science student who builds reliable APIs.",
        experience=[ExperienceItem(company="Acme", role="SWE Intern", start="May 2025", end="Jul 2025",
                                   bullets=["Built a REST API in Python that reduced report time by 40%.",
                                            "Implemented unit tests improving coverage for the billing module."])],
        projects=[ProjectItem(name="Resumo", tech=["FastAPI", "React"],
                              bullets=["Implemented a parser registry supporting 10 formats.",
                                       "Designed a scoring engine with transparent, testable rules."])],
        education=[EducationItem(institution="IIT Example", degree="B.Tech CSE", start="2022", end="2026")],
        skills=[SkillGroup(category="Languages", items=["Python", "TypeScript"])],
    )


def _weak_resume() -> ResumeContent:
    return ResumeContent(
        contact=ResumeContact(name="", email="not-an-email", phone="", links=[]),
        summary="",
        experience=[ExperienceItem(company="Acme", role="Intern",
                                   bullets=["Responsible for various things.", "I helped with stuff."])],
        projects=[],
        education=[],
        skills=[SkillGroup(category="Skills", items=["COBOL", "Fortran"])],
    )


def test_good_resume_scores_higher_than_weak():
    good = analyze_quality(_good_resume())
    weak = analyze_quality(_weak_resume())
    assert good.overall_score > weak.overall_score


def test_score_is_in_range():
    result = analyze_quality(_good_resume())
    assert 0 <= result.overall_score <= 10
    assert all(0 <= v <= 10 for v in result.category_scores.values())


def test_weak_phrasing_detected_with_excerpt():
    result = analyze_quality(_weak_resume())
    writing = [f for f in result.findings if f.category == "writing"]
    assert any("Responsible for" in (f.title + (f.excerpt or "")) or "weak" in f.title.lower() for f in writing
               ) or any(f.severity == "important" for f in writing)
    assert result.overall_score < 6


def test_contact_problems_flagged():
    result = analyze_quality(_weak_resume())
    categories = {f.category for f in result.findings}
    assert "contact" in categories
    assert any(f.severity == "critical" for f in result.findings)


def test_student_without_experience_not_penalised_as_professional():
    student = ResumeContent(
        contact=ResumeContact(name="X", email="x@example.com", phone="1", links=[{"label": "GitHub", "url": "https://github.com/x"}]),
        summary="Aspiring developer.",
        projects=[ProjectItem(name="App", tech=["React"], bullets=["Built a responsive app used by classmates."])],
        education=[EducationItem(institution="College", degree="B.Tech", start="2022", end="2026")],
        skills=[SkillGroup(category="Skills", items=["React"])],
    )
    result = analyze_quality(student)
    assert result.overall_score >= 4.0
    assert "structure" in result.category_scores


def test_findings_have_explanations():
    result = analyze_quality(_good_resume())
    for finding in result.findings:
        assert finding.explanation
