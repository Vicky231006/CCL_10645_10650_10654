"""Deterministic resume-quality engine.

Scores are computed from transparent rules only. AI, when enabled, adds separately
labelled qualitative commentary and never changes the deterministic score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.schemas.resume import ResumeContent

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "helped to", "assisted with",
    "participated in", "involved in", "duties included", "tasked with",
    "in charge of", "was part of", "worked with", "assisted in",
]
FILLER_WORDS = ["various", "several", "many", "stuff", "things", "etc", "some", "a lot of", "stuff like"]
FIRST_PERSON = re.compile(r"(?:^|\s)(i|my|me|we|our)\s", re.I)
ACTION_VERBS = {
    "built", "developed", "designed", "implemented", "led", "created", "engineered", "optimized",
    "improved", "reduced", "increased", "automated", "deployed", "architected", "launched",
    "migrated", "refactored", "integrated", "tested", "analyzed", "delivered", "shipped",
    "achieved", "scaled", "trained", "published", "researched", "designed", "constructed",
    "implemented", "debugged", "documented", "coordinated", "mentored", "won",
}
COMMON_MISSPELLINGS = {
    "recieve": "receive", "seperate": "separate", "definately": "definitely",
    "occured": "occurred", "sucess": "success", "acheive": "achieve",
    "managment": "management", "enviroment": "environment", "responsibilty": "responsibility",
    "experiance": "experience", "univeristy": "university", "baccalaureate": "baccalaureate",
    "compatability": "compatibility", "dependancy": "dependency", "maintainance": "maintenance",
}
REPEATED_WORD_RE = re.compile(r"\b(\w+)\s+\1\b", re.I)
MALFORMED_URL_RE = re.compile(r"https?://\s|http://[^\s]*\s|www\.\s", re.I)


@dataclass
class Finding:
    category: str
    severity: str  # critical | important | polish
    title: str
    excerpt: str | None = None
    explanation: str | None = None
    suggestion: str | None = None
    location: str | None = None


@dataclass
class QualityResult:
    overall_score: float
    category_scores: dict[str, float]
    findings: list[Finding] = field(default_factory=list)
    methodology: str = ""


CATEGORY_WEIGHTS = {
    "contact": 0.12,
    "structure": 0.18,
    "writing": 0.22,
    "impact": 0.20,
    "skills_evidence": 0.14,
    "consistency": 0.14,
}

METHODOLOGY = (
    "Scores are produced by deterministic rules over the structured resume: contact completeness, "
    "section coverage relative to career stage, weak/vague phrasing, action-verb and measurable-outcome "
    "usage, skill-evidence support, and consistency of dates and formatting. Category scores are 0-10; the "
    "overall score is their weighted average (weights: contact 12%, structure 18%, writing 22%, impact 20%, "
    "skills-evidence 14%, consistency 14%). This is an advisory assessment of resume quality, NOT an ATS "
    "score or a probability of being hired. Missing information is handled fairly: candidates without "
    "work experience are evaluated on projects, coursework and demonstrated skills instead."
)


def _iter_bullets(content: ResumeContent) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for i, exp in enumerate(content.experience):
        for j, b in enumerate(exp.bullets):
            out.append((f"Experience {i + 1} · bullet {j + 1}", b))
    for i, proj in enumerate(content.projects):
        for j, b in enumerate(proj.bullets):
            out.append((f"Project {i + 1} · bullet {j + 1}", b))
    return out


def _clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def _score_contact(content: ResumeContent, findings: list[Finding]) -> float:
    contact = content.contact
    score = 10.0
    if not contact.email:
        score -= 3
        findings.append(Finding("contact", "critical", "Missing email address", None,
                                "Recruiters need an email to contact you.", "Add a professional email."))
    elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", contact.email):
        score -= 2
        findings.append(Finding("contact", "important", "Email address looks malformed", contact.email,
                                "An invalid email may block contact.", "Correct the email address."))
    if not contact.phone:
        score -= 1.5
        findings.append(Finding("contact", "important", "Missing phone number", None,
                                "Many recruiters prefer a direct phone contact.", "Add a phone number with country code."))
    if not contact.name:
        score -= 2
        findings.append(Finding("contact", "critical", "Missing name", None,
                                "A resume without a name is unusable.", "Add your full name at the top."))
    if not contact.links:
        score -= 1
        findings.append(Finding("contact", "polish", "No professional links", None,
                                "GitHub/LinkedIn links strengthen a technical profile.",
                                "Add a GitHub and/or LinkedIn link."))
    else:
        for link in contact.links:
            if MALFORMED_URL_RE.search(link.url or ""):
                score -= 0.5
                findings.append(Finding("contact", "important", "Malformed link", link.url,
                                        "A broken link looks careless.", "Fix or remove this link."))
    return _clamp(score)


def _score_structure(content: ResumeContent, findings: list[Finding], has_experience: bool) -> float:
    score = 6.0
    if content.summary:
        score += 1.0
    else:
        score -= 0.5
        findings.append(Finding("structure", "polish", "No summary/objective", None,
                                "A short summary helps recruiters orient quickly.",
                                "Add a 2-3 line summary tailored to your target role."))
    if content.experience:
        score += 1.5
    elif has_experience:
        findings.append(Finding("structure", "important", "No experience section", None,
                                "You indicated experience but none appears.", "Add internships/work entries."))
    if content.projects:
        score += 1.5
    else:
        findings.append(Finding("structure", "important", "No projects section", None,
                                "For early-career candidates, projects are key evidence.",
                                "Add 2-3 technical projects with outcomes."))
    if content.education:
        score += 1.0
    else:
        findings.append(Finding("structure", "critical", "No education section", None,
                                "Education is expected for students and recent graduates.",
                                "Add your degree, institution and graduation year."))
    if content.skills:
        score += 0.5
    else:
        findings.append(Finding("structure", "important", "No skills section", None,
                                "A concise skills list aids keyword matching.",
                                "Add grouped technical skills."))
    if not content.experience and not content.projects and not has_experience:
        score -= 2
        findings.append(Finding("structure", "critical", "No experience or projects", None,
                                "There is little evidence of your abilities.",
                                "Add projects, coursework, or internships to demonstrate skills."))
    return _clamp(score)


def _score_writing(content: ResumeContent, findings: list[Finding]) -> float:
    bullets = _iter_bullets(content)
    if not bullets:
        findings.append(Finding("writing", "important", "No bullet points to review", None,
                                "Bullet points communicate achievements clearly.",
                                "Write 2-4 bullet points per role/project."))
        return 5.0
    penalty = 0.0
    weak_count = 0
    for loc, text in bullets:
        low = text.lower()
        for phrase in WEAK_PHRASES:
            if low.startswith(phrase) or f" {phrase} " in f" {low} ":
                weak_count += 1
                penalty += 0.4
                findings.append(Finding(
                    "writing", "important", f"Weak/vague phrasing: '{phrase}'", text,
                    "Phrases like this describe duties, not achievements, and weaken impact.",
                    "Start with a strong action verb and state the outcome.",
                    loc,
                ))
                break
        if FIRST_PERSON.search(text):
            penalty += 0.3
            findings.append(Finding("writing", "polish", "First-person pronoun", text,
                                    "Resumes conventionally omit 'I/we'.", "Remove first-person pronouns.", loc))
        for filler in FILLER_WORDS:
            if f" {filler} " in f" {low} ":
                penalty += 0.2
                findings.append(Finding("writing", "polish", f"Filler word: '{filler}'", text,
                                        "Vague quantifiers dilute specificity.", "Replace with precise detail.", loc))
                break
        m = REPEATED_WORD_RE.search(text)
        if m:
            penalty += 0.3
            findings.append(Finding("writing", "important", f"Repeated word: '{m.group(1)}'", text,
                                    "Repeated words are usually typos.", "Remove the duplicate word.", loc))
        for wrong, right in COMMON_MISSPELLINGS.items():
            if re.search(rf"\b{wrong}\b", low):
                penalty += 0.5
                findings.append(Finding("writing", "important", f"Possible misspelling: '{wrong}'", text,
                                        f"'{wrong}' is a common misspelling.", f"Replace with '{right}'.", loc))
    # reward action verbs
    verb_hits = sum(1 for _, t in bullets if re.match(r"^\W*([A-Za-z]+)", t) and
                    re.match(r"^\W*([A-Za-z]+)", t).group(1).lower() in ACTION_VERBS)
    verb_ratio = verb_hits / len(bullets)
    base = 6.0 + verb_ratio * 2.0
    if weak_count == 0:
        base += 1.0
    return _clamp(base - penalty * 0.2)


def _score_impact(content: ResumeContent, findings: list[Finding]) -> float:
    bullets = _iter_bullets(content)
    if not bullets:
        return 5.0
    with_metric = sum(1 for _, t in bullets if re.search(r"\d", t))
    tech_detail = sum(1 for _, t in bullets if re.search(r"\b(using|with|via|built|implemented|api|database|model)\b", t, re.I))
    metric_ratio = with_metric / len(bullets)
    score = 3.0 + metric_ratio * 5.0 + (tech_detail / len(bullets)) * 2.0
    if metric_ratio < 0.25:
        findings.append(Finding(
            "impact", "important", "Few bullets show measurable outcomes", None,
            "Quantified results are far more convincing (numbers, %, time saved, scale).",
            "Where truthful, add real metrics. Do not invent numbers.",
        ))
    return _clamp(score)


def _score_skills_evidence(content: ResumeContent, findings: list[Finding]) -> float:
    skills = [s.strip().lower() for group in content.skills for s in group.items if s.strip()]
    if not skills:
        return 6.0
    body = content.all_text().lower()
    unsupported = []
    for skill in skills:
        if skill and skill not in body.replace(skill, "", 1):
            # appears only in the skills list, not elsewhere
            occurrences = body.count(skill)
            if occurrences <= 1:
                unsupported.append(skill)
    if unsupported:
        for skill in unsupported[:8]:
            findings.append(Finding(
                "skills_evidence", "polish", f"Skill not evidenced: '{skill}'", skill,
                "A skill listed but never demonstrated reads as padding.",
                "Show where you used it in a project or experience bullet, or remove it.",
                "Skills",
            ))
    ratio = 1 - (len(unsupported) / len(skills))
    return _clamp(4.0 + ratio * 6.0)


def _score_consistency(content: ResumeContent, findings: list[Finding]) -> float:
    score = 9.0
    dates: list[str] = []
    for exp in content.experience:
        dates += [d for d in (exp.start, exp.end) if d]
    for ed in content.education:
        dates += [d for d in (ed.start, ed.end) if d]
    years = [re.search(r"\d{4}", d).group(0) for d in dates if re.search(r"\d{4}", d)]
    if years:
        ints = [int(y) for y in years]
        if max(ints) - min(ints) > 45:
            score -= 1.5
            findings.append(Finding("consistency", "important", "Implausible date range", f"{min(ints)}–{max(ints)}",
                                    "Dates look inconsistent.", "Double-check all dates."))
    if dates:
        has_word_dates = any(re.search(r"[A-Za-z]{3}", d) for d in dates)
        has_numeric_dates = any(re.fullmatch(r"\d{4}", d.strip()) for d in dates)
        if has_word_dates and has_numeric_dates:
            score -= 0.8
            findings.append(Finding("consistency", "polish", "Inconsistent date formats", None,
                                    "Mixed date formats look untidy.",
                                    "Use one date format consistently, e.g. 'Jan 2024'."))
    # consistent capitalisation of section-like content
    return _clamp(score)


def analyze_quality(content: ResumeContent, *, target_role: str | None = None) -> QualityResult:
    findings: list[Finding] = []
    has_experience = bool(content.experience)
    scores = {
        "contact": _score_contact(content, findings),
        "structure": _score_structure(content, findings, has_experience),
        "writing": _score_writing(content, findings),
        "impact": _score_impact(content, findings),
        "skills_evidence": _score_skills_evidence(content, findings),
        "consistency": _score_consistency(content, findings),
    }
    overall = sum(scores[k] * CATEGORY_WEIGHTS[k] for k in CATEGORY_WEIGHTS)
    if target_role:
        findings.append(Finding(
            "structure", "polish", f"Tailoring to target role: {target_role}", None,
            "A resume aligned to a specific role performs better.",
            f"Reorder sections and emphasise skills relevant to {target_role}.",
        ))
    return QualityResult(
        overall_score=round(overall, 1),
        category_scores={k: round(v, 1) for k, v in scores.items()},
        findings=findings,
        methodology=METHODOLOGY,
    )
