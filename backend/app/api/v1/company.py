"""Source-grounded company research routes."""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.core.errors import NotFoundError, ValidationAppError
from app.models import CompanyCitation, CompanyResearch, User
from app.schemas.career import CompanyCitationOut, CompanyResearchOut, CompanyResearchRequest
from app.services.ai.service import ai_company_research
from app.services.research import fetch_source

router = APIRouter(prefix="/company-research", tags=["company-research"])

STOPWORDS = set(
    "the a an and or of to in for with on at by from as is are be we you our their this that it its "
    "will can have has using use used will be able about across into your".split()
)


def _research_out(research: CompanyResearch) -> CompanyResearchOut:
    return CompanyResearchOut(
        id=research.id, company=research.company, target_role=research.target_role, summary=research.summary,
        themes=research.themes, patterns=research.patterns, confidence=research.confidence,
        citations=[CompanyCitationOut.model_validate(c) for c in research.citations], created_at=research.created_at,
    )


@router.post("", response_model=CompanyResearchOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_research(payload: CompanyResearchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CompanyResearchOut:
    sources = []
    for url in payload.source_urls[:8]:
        source = fetch_source(url)
        sources.append(source)

    successful = [s for s in sources if s.text and not s.error]
    if not successful:
        raise ValidationAppError(
            "No usable public sources could be retrieved. Provide official careers/engineering URLs, "
            "or note that some sites block automated retrieval.",
            code="no_sources",
        )

    # deterministic theme extraction from the retrieved text
    tokens = Counter()
    for s in successful:
        for word in re.findall(r"[A-Za-z][A-Za-z+#.]+", s.text.lower()):
            if word in STOPWORDS or len(word) < 3:
                continue
            tokens[word] += 1
    themes = [word for word, count in tokens.most_common(15) if count >= 2][:10]

    summary = (
        f"Based on {len(successful)} public source(s) for {payload.company}, recurring terms include: "
        f"{', '.join(themes[:8]) or 'n/a'}. This is an aggregate of publicly available text, not a claim about "
        "any individual employee."
    )
    confidence = "verified" if successful else "inference"
    themes_list = themes
    patterns: list[str] = [
        f"Frequent terms across public pages: {', '.join(themes[:8])}",
        "Individual examples are only shown when they are published publicly and appropriately.",
    ]
    ai_used = False
    if payload.use_ai and settings.llm_provider != "none":
        joined = "\n\n".join(f"[{s.label}] {s.excerpt}" for s in successful)
        try:
            ai = ai_company_research(payload.company, payload.target_role, joined)
            if ai.get("summary"):
                summary = ai["summary"]
            if ai.get("themes"):
                themes_list = [str(t) for t in ai["themes"]][:10]
            if ai.get("patterns"):
                patterns = [str(p) for p in ai["patterns"]][:8]
            ai_used = True
        except Exception:  # noqa: BLE001
            ai_used = False

    research = CompanyResearch(
        user_id=user.id, company=payload.company, target_role=payload.target_role,
        summary=summary, themes=themes_list, patterns=patterns,
        confidence="inference" if ai_used else confidence,
    )
    db.add(research)
    db.flush()
    for s in sources:
        db.add(CompanyCitation(
            research_id=research.id, label=s.label or s.url, url=s.url,
            source_type="public", retrieved_at=datetime.now(timezone.utc).isoformat(),
            excerpt=(s.text[:400] if s.text else (s.error or "")),
        ))
    db.commit()
    db.refresh(research)
    return _research_out(research)


@router.get("", response_model=list[CompanyResearchOut])
def list_research(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[CompanyResearchOut]:
    rows = db.scalars(select(CompanyResearch).where(CompanyResearch.user_id == user.id).order_by(CompanyResearch.created_at.desc())).all()
    return [_research_out(r) for r in rows]


@router.get("/{research_id}", response_model=CompanyResearchOut)
def get_research(research_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CompanyResearchOut:
    research = db.get(CompanyResearch, research_id)
    if not research or research.user_id != user.id:
        raise NotFoundError("Research not found.")
    return _research_out(research)
