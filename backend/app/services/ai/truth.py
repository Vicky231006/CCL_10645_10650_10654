"""Truth-preservation checks for AI-generated suggestions.

Any AI suggestion is verified against the candidate's source facts before it can be
applied. Checks reject invented metrics, dates, and unsupported technologies.
"""
from __future__ import annotations

import re

NUMBER_RE = re.compile(r"\b\d[\d,.]*\b")
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
MONTH_RE = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b", re.I
)

TECH_LEXICON = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin", "swift",
    "react", "angular", "vue", "svelte", "next.js", "node.js", "express", "django", "flask",
    "fastapi", "spring", "rails", "laravel", "graphql", "rest", "grpc",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite", "dynamodb", "cassandra",
    "docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions", "gitlab ci",
    "aws", "azure", "gcp", "lambda", "ec2", "s3", "rds",
    "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "opencv",
    "spark", "hadoop", "kafka", "airflow", "dbt", "tableau", "power bi",
    "html", "css", "tailwind", "sass", "figma", "git", "linux", "bash",
    "elasticsearch", "nginx", "rabbitmq", "celery", "websockets", "oauth", "jwt",
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9+#.]+", text.lower()))


def verify_suggestion(original: str, proposed: str, source_text: str) -> tuple[bool, list[str]]:
    """Return (verified, flags). `verified=False` means it must not be auto-applied."""
    flags: list[str] = []
    source_low = source_text.lower()

    # 1. invented numbers / metrics
    for num in NUMBER_RE.findall(proposed):
        if num not in source_text:
            flags.append(f"References a number '{num}' not found in your resume.")

    # 2. invented years/dates
    for year in YEAR_RE.findall(proposed):
        if year not in source_text:
            flags.append(f"References a year '{year}' not found in your resume.")
    source_months = {m.lower()[:3] for m in MONTH_RE.findall(source_text)}
    for month in MONTH_RE.findall(proposed):
        if month.lower()[:3] not in source_months:
            flags.append(f"References a month '{month}' not found in your resume.")

    # 3. unsupported technologies
    src_tokens = _tokens(source_text)
    prop_tokens = _tokens(proposed)
    for tech in TECH_LEXICON & prop_tokens:
        if tech not in src_tokens:
            flags.append(f"Introduces technology '{tech}' not present in your resume.")

    return (len(flags) == 0), flags


def unsupported_claims(proposed: str, source_text: str) -> list[str]:
    _, flags = verify_suggestion("", proposed, source_text)
    return flags
