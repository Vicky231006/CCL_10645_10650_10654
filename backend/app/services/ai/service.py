"""High-level AI service functions. All return validated Python structures."""
from __future__ import annotations

from app.core.errors import AiUnavailableError
from app.core.logging import get_logger
from app.services.ai import prompts
from app.services.ai.providers import extract_json, get_provider

logger = get_logger("resumo.ai.service")


def _generate_json(prompt: str) -> dict | list:
    provider = get_provider()
    raw = provider.generate(prompt, system=prompts.SYSTEM_PROMPT, json_mode=True)
    data = extract_json(raw)
    if data is None:
        raise AiUnavailableError("The AI provider returned a response that could not be parsed.")
    return data


def ai_quality_commentary(resume_text: str, target_role: str | None) -> dict:
    data = _generate_json(prompts.quality_review_prompt(resume_text, target_role))
    if not isinstance(data, dict):
        raise AiUnavailableError("Unexpected AI response shape.")
    return {
        "strengths": [str(s) for s in data.get("strengths", [])][:10],
        "weaknesses": [str(s) for s in data.get("weaknesses", [])][:10],
        "top_actions": [str(s) for s in data.get("top_actions", [])][:5],
    }


def ai_extract_jd(job_text: str) -> dict:
    data = _generate_json(prompts.jd_extraction_prompt(job_text))
    if not isinstance(data, dict):
        raise AiUnavailableError("Unexpected AI response shape.")
    return data


def ai_rewrite_bullets(resume_text: str, job_text: str, bullets: list[str]) -> list[dict]:
    data = _generate_json(prompts.bullet_rewrite_prompt(resume_text, job_text, bullets))
    suggestions = data.get("suggestions") if isinstance(data, dict) else data
    if not isinstance(suggestions, list):
        raise AiUnavailableError("Unexpected AI response shape.")
    return [s for s in suggestions if isinstance(s, dict)]


def ai_gap_analysis(resume_text: str, job_text: str) -> dict:
    data = _generate_json(prompts.gap_analysis_prompt(resume_text, job_text))
    if not isinstance(data, dict):
        raise AiUnavailableError("Unexpected AI response shape.")
    return data


def ai_project_plan(resume_text: str, job_text: str, title: str) -> dict:
    data = _generate_json(prompts.project_plan_prompt(resume_text, job_text, title))
    if not isinstance(data, dict):
        raise AiUnavailableError("Unexpected AI response shape.")
    return data


def ai_generate_asset(kind: str, context: str) -> str:
    provider = get_provider()
    return provider.generate(prompts.asset_generation_prompt(kind, context), system=prompts.SYSTEM_PROMPT)


def ai_company_research(company: str, role: str | None, sources: str) -> dict:
    data = _generate_json(prompts.company_research_prompt(company, role, sources))
    if not isinstance(data, dict):
        raise AiUnavailableError("Unexpected AI response shape.")
    return data
