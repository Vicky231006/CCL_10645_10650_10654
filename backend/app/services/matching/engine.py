"""Deterministic keyword extraction and resume-to-job matching.

Uses exact + normalised matching (with a synonym map). AI may augment JD extraction but
this deterministic path always works and is the source of truth for the match score.
"""
from __future__ import annotations

import re

from app.schemas.resume import ResumeContent

SKILL_LEXICON: dict[str, list[str]] = {
    "python": ["python"], "java": ["java"], "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"], "c": ["c"], "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp", ".net"], "go": ["golang", "go"],
    "rust": ["rust"], "kotlin": ["kotlin"], "swift": ["swift"], "ruby": ["ruby"],
    "php": ["php"], "scala": ["scala"], "r": ["r language"],
    "react": ["react", "react.js", "reactjs"], "angular": ["angular"],
    "vue": ["vue", "vue.js", "vuejs"], "svelte": ["svelte"], "next.js": ["next.js", "nextjs"],
    "node.js": ["node.js", "nodejs", "node"], "express": ["express", "express.js"],
    "django": ["django"], "flask": ["flask"], "fastapi": ["fastapi"],
    "spring": ["spring", "spring boot"], "rails": ["rails", "ruby on rails"],
    "graphql": ["graphql"], "rest": ["rest", "rest api", "restful"], "grpc": ["grpc"],
    "sql": ["sql"], "postgresql": ["postgresql", "postgres"], "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"], "redis": ["redis"], "sqlite": ["sqlite"],
    "dynamodb": ["dynamodb"], "cassandra": ["cassandra"], "oracle": ["oracle db"],
    "docker": ["docker"], "kubernetes": ["kubernetes", "k8s"], "terraform": ["terraform"],
    "ansible": ["ansible"], "jenkins": ["jenkins"], "github actions": ["github actions"],
    "gitlab ci": ["gitlab ci"], "ci/cd": ["ci/cd", "cicd", "continuous integration"],
    "aws": ["aws", "amazon web services"], "azure": ["azure"], "gcp": ["gcp", "google cloud"],
    "lambda": ["lambda", "aws lambda"], "ec2": ["ec2"], "s3": ["s3"], "rds": ["rds"],
    "machine learning": ["machine learning", "ml"], "deep learning": ["deep learning"],
    "pytorch": ["pytorch"], "tensorflow": ["tensorflow"], "keras": ["keras"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"], "pandas": ["pandas"],
    "numpy": ["numpy"], "opencv": ["opencv"], "nlp": ["nlp", "natural language processing"],
    "computer vision": ["computer vision", "cv"],
    "spark": ["spark", "apache spark"], "hadoop": ["hadoop"], "kafka": ["kafka"],
    "airflow": ["airflow"], "dbt": ["dbt"], "tableau": ["tableau"], "power bi": ["power bi"],
    "html": ["html"], "css": ["css"], "tailwind": ["tailwind", "tailwindcss"],
    "git": ["git"], "linux": ["linux", "unix"], "bash": ["bash", "shell scripting"],
    "elasticsearch": ["elasticsearch"], "nginx": ["nginx"], "rabbitmq": ["rabbitmq"],
    "celery": ["celery"], "websockets": ["websocket", "websockets"],
    "oauth": ["oauth"], "jwt": ["jwt"], "unit testing": ["unit testing", "unit tests"],
    "data structures": ["data structures"], "algorithms": ["algorithms"],
    "object oriented": ["object oriented", "oop"], "agile": ["agile", "scrum"],
    "system design": ["system design"], "microservices": ["microservices"],
}

# canonical -> accepted equivalents
SYNONYMS: dict[str, set[str]] = {
    "javascript": {"js", "javascript"},
    "typescript": {"ts", "typescript"},
    "postgresql": {"postgres", "psql", "postgresql"},
    "node.js": {"node", "nodejs", "node.js"},
    "kubernetes": {"k8s", "kubernetes"},
    "machine learning": {"ml", "machine learning", "machine-learning"},
    "ci/cd": {"ci/cd", "cicd", "continuous integration", "continuous delivery"},
    "go": {"golang", "go"},
    "c++": {"cpp", "c++"},
    "c#": {"csharp", "c#", ".net"},
    "react": {"react", "reactjs", "react.js"},
    "aws": {"aws", "amazon web services"},
    "gcp": {"gcp", "google cloud", "google cloud platform"},
    "unit testing": {"unit testing", "unit tests", "unit test"},
    "object oriented": {"oop", "object oriented", "object-oriented"},
}

CATEGORY_HINTS: dict[str, str] = {
    "cloud": "cloud", "aws": "cloud", "azure": "cloud", "gcp": "cloud",
    "machine learning": "ai/ml", "deep learning": "ai/ml", "pytorch": "ai/ml",
    "tensorflow": "ai/ml", "nlp": "ai/ml", "computer vision": "ai/ml",
    "docker": "devops", "kubernetes": "devops", "terraform": "devops", "jenkins": "devops",
    "sql": "database", "postgresql": "database", "mongodb": "database", "mysql": "database",
}

REQUIRED_CUES = ["required", "must have", "must-have", "requirements", "you will need", "minimum", "essential"]
PREFERRED_CUES = ["preferred", "nice to have", "nice-to-have", "plus", "bonus", "desirable", "advantage", "good to have"]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _importance_for_context(context: str) -> str:
    low = context.lower()
    if any(cue in low for cue in REQUIRED_CUES):
        return "required"
    if any(cue in low for cue in PREFERRED_CUES):
        return "preferred"
    return "bonus"


def extract_keywords(job_text: str) -> list[dict]:
    """Extract keywords with importance + category from raw JD text."""
    text = _normalise(job_text)
    lines = [ln.strip() for ln in job_text.splitlines() if ln.strip()]
    # Track a rolling "importance context" from the most recent cue-bearing line.
    context = ""
    seen: dict[str, dict] = {}
    for line in lines:
        line_low = line.lower().strip(":•-* ")
        if any(cue in line_low for cue in REQUIRED_CUES + PREFERRED_CUES) and len(line_low) < 60:
            context = line_low
        for canonical, variants in SKILL_LEXICON.items():
            for variant in variants:
                if re.search(rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])", line_low):
                    importance = _importance_for_context(context)
                    entry = seen.setdefault(
                        canonical,
                        {
                            "keyword": canonical,
                            "importance": importance,
                            "category": CATEGORY_HINTS.get(canonical, "skill"),
                        },
                    )
                    # required beats preferred beats bonus
                    order = {"required": 3, "preferred": 2, "bonus": 1}
                    if order[importance] > order[entry["importance"]]:
                        entry["importance"] = importance
                    break
    return sorted(seen.values(), key=lambda k: (-{"required": 3, "preferred": 2, "bonus": 1}[k["importance"]], k["keyword"]))


def parse_job(text: str) -> dict:
    """Deterministic JD parsing into the ParsedJob shape."""
    keywords = extract_keywords(text)
    required = [k["keyword"] for k in keywords if k["importance"] == "required"]
    preferred = [k["keyword"] for k in keywords if k["importance"] == "preferred"]
    bonus = [k["keyword"] for k in keywords if k["importance"] == "bonus"]
    responsibilities: list[str] = []
    qualifications: list[str] = []
    for line in text.splitlines():
        clean = line.strip("•-* \t")
        if len(clean) < 15:
            continue
        low = clean.lower()
        if low.startswith("responsibilities"):
            remainder = clean.split(":", 1)[-1].strip() if ":" in clean else ""
            if len(remainder) >= 15:
                responsibilities.append(remainder[:200])
            continue
        if low.startswith(("you will", "the role", "what you")):
            continue
        if re.match(r"^(build|develop|design|implement|collaborate|maintain|create|write|analyz|analys)", low):
            responsibilities.append(clean[:200])
        elif re.match(r"^(bachelor|master|degree|pursuing|currently enrolled|graduat)", low):
            qualifications.append(clean[:200])
    years = re.search(r"(\d+)\+?\s*(?:years|yrs)", text, re.I)
    seniority = None
    low = text.lower()
    if re.search(r"\bintern(ship)?\b", low):
        seniority = "intern"
    elif re.search(r"\b(entry[- ]level|new grad|graduate)\b", low):
        seniority = "entry"
    elif re.search(r"\bsenior\b", low):
        seniority = "senior"
    return {
        "required_skills": required,
        "preferred_skills": preferred,
        "tools": bonus[:12],
        "responsibilities": responsibilities[:10],
        "qualifications": qualifications[:8],
        "experience_years": f"{years.group(1)}+ years" if years else None,
        "domain": [],
        "certifications": [],
        "terminology": [],
        "seniority": seniority,
    }


def _resume_evidence(content: ResumeContent) -> tuple[str, str, str]:
    """Return (all_text, strong_text (bullets), skills_text)."""
    all_parts: list[str] = [content.summary]
    strong: list[str] = []
    for e in content.experience:
        all_parts += [e.company, e.role]
        strong += e.bullets
        all_parts += e.bullets
    for p in content.projects:
        all_parts += [p.name, *p.tech]
        strong += p.bullets
        all_parts += p.bullets
    for ed in content.education:
        all_parts += [ed.institution, ed.degree, *ed.details]
    skills_text = " ".join(s for g in content.skills for s in g.items)
    all_parts.append(skills_text)
    all_parts += content.certifications + content.achievements
    return "\n".join(all_parts).lower(), "\n".join(strong).lower(), skills_text.lower()


def _variants(keyword: str) -> set[str]:
    return SYNONYMS.get(keyword, {keyword}) | {keyword}


def _find_evidence(keyword: str, content: ResumeContent) -> tuple[str, str | None, str | None]:
    """Return (status, location, excerpt) for a keyword."""
    variants = _variants(keyword)
    pattern = "|".join(re.escape(v) for v in variants)

    def hit(text: str) -> bool:
        return bool(re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", text, re.I))

    for i, exp in enumerate(content.experience):
        for b in exp.bullets:
            if hit(b):
                return "found", f"Experience {i + 1}", b[:200]
    for i, proj in enumerate(content.projects):
        for b in proj.bullets:
            if hit(b):
                return "found", f"Project {i + 1}", b[:200]
        if hit(proj.name) or any(hit(t) for t in proj.tech):
            return "found", f"Project {i + 1}", proj.name[:200]
    skills_text = " ".join(s for g in content.skills for s in g.items)
    if hit(skills_text):
        return "weak", "Skills", keyword
    all_text, _, _ = _resume_evidence(content)
    if hit(all_text):
        return "weak", "Resume", keyword
    return "missing", None, None


IMPORTANCE_WEIGHT = {"required": 3.0, "preferred": 2.0, "bonus": 1.0}
STATUS_VALUE = {"found": 1.0, "weak": 0.5, "missing": 0.0}


def match_resume(content: ResumeContent, keywords: list[dict]) -> dict:
    evidence: list[dict] = []
    total_weight = 0.0
    earned = 0.0
    required_missing: list[str] = []
    for kw in keywords:
        status, location, excerpt = _find_evidence(kw["keyword"], content)
        weight = IMPORTANCE_WEIGHT.get(kw["importance"], 1.0)
        total_weight += weight
        earned += weight * STATUS_VALUE[status]
        if status == "missing" and kw["importance"] == "required":
            required_missing.append(kw["keyword"])
        action = {
            "found": "No change needed — already evidenced.",
            "weak": "Strengthen: show where you actually used this, ideally in a project or experience bullet.",
            "missing": "Gap: do not invent it. Build or document real evidence, or omit if not essential.",
        }[status]
        evidence.append(
            {
                "keyword": kw["keyword"],
                "importance": kw["importance"],
                "category": kw.get("category", "skill"),
                "status": status,
                "evidence_location": location,
                "evidence_excerpt": excerpt,
                "recommended_action": action,
            }
        )
    coverage = round(earned / total_weight, 3) if total_weight else 0.0
    overall = round(coverage * 100, 1)
    found = [e for e in evidence if e["status"] == "found"]
    breakdown = {
        "keywords_total": len(evidence),
        "found": len(found),
        "weak": len([e for e in evidence if e["status"] == "weak"]),
        "missing": len([e for e in evidence if e["status"] == "missing"]),
        "required_missing": required_missing,
        "strongest_sections": sorted({e["evidence_location"] for e in found if e["evidence_location"]})[:5],
    }
    methodology = (
        "Alignment score = weighted coverage of job keywords evidenced in the resume. Each keyword is "
        "weighted by importance (required ×3, preferred ×2, bonus ×1). Evidenced in an experience/project "
        "bullet counts 1.0; present only in the skills list or elsewhere counts 0.5; absent counts 0. "
        "Equivalent terms are normalised (e.g. JS=JavaScript) but distinct technologies are never merged. "
        "This is an advisory alignment estimate, NOT an employer's ATS score."
    )
    return {"overall_score": overall, "coverage": coverage, "breakdown": breakdown,
            "evidence": evidence, "methodology": methodology}
