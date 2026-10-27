"""Heuristic structuring: raw extracted text -> ResumeContent.

Parsers do not promise perfect extraction. This produces a best-effort structured
model with clear confidence; users can correct everything afterwards.
"""
from __future__ import annotations

import re

from app.schemas.resume import (
    EducationItem,
    ExperienceItem,
    LinkItem,
    ProjectItem,
    ResumeContact,
    ResumeContent,
    SkillGroup,
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.\-]?)?(?:\(?\d{2,5}\)?[\s.\-]?)\d{3}[\s.\-]?\d{3,4}")
URL_RE = re.compile(r"https?://[^\s)>\]]+|(?:www\.)[^\s)>\]]+")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s)>\]]+", re.I)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[^\s)>\]]+", re.I)
_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"
DATE_RE = re.compile(
    rf"({_MONTH}\s*\d{{4}}|\d{{4}})\s*(?:-|–|to|—)\s*({_MONTH}\s*\d{{4}}|\d{{4}}|Present|Current)",
    re.I,
)
SINGLE_DATE_RE = re.compile(rf"{_MONTH}\s*\d{{4}}|\b(?:19|20)\d{{2}}\b", re.I)
BULLET_CHARS = "\u2022\u2023\u25CF\u25AA\u25AB\u2013\u2014\u00b7\u2043\uf0b7\uf0a7\uf076\uf0d8"
BULLET_PREFIX = re.compile(rf"^\s*(?:[{BULLET_CHARS}\-\*\+]\s*|o\s+|\(?\d+[.)]\s+)")

INSTITUTION_HINT = re.compile(
    r"\b(college|university|institute|institution|school|academy|polytechnic|vidyalaya|iit|nit|iiit|bits)",
    re.I,
)
DEGREE_HINT = re.compile(
    r"\b(b\.?\s?tech|b\.?\s?e\.?|b\.?\s?sc|b\.?\s?c\.?\s?a|b\.?\s?com|m\.?\s?tech|m\.?\s?sc|mba|mca|m\.?\s?com|"
    r"bachelor|master|phd|doctorate|diploma|hsc|ssc|cgpa|gpa|cpi|percentage|intermediate|higher secondary|"
    r"senior secondary|secondary|12th|10th)\b",
    re.I,
)

SECTION_ALIASES: dict[str, list[str]] = {
    "summary": ["summary", "objective", "profile", "about", "professional summary", "career objective"],
    "experience": [
        "experience", "work experience", "professional experience", "employment",
        "internship", "internships", "work history", "relevant experience",
    ],
    "projects": ["projects", "project experience", "personal projects", "academic projects", "selected projects"],
    "education": ["education", "academics", "academic background", "academic qualifications", "education & training"],
    "skills": ["skills", "technical skills", "technologies", "tech stack", "technical proficiencies", "core competencies"],
    "certifications": ["certifications", "certificates", "licenses", "certifications & courses"],
    "achievements": [
        "achievements", "awards", "honors", "honours", "accomplishments",
        "extracurricular", "extracurricular activities", "co-curricular", "co curricular",
        "leadership", "leadership experience", "publications", "activities", "activity",
        "hackathons", "hackathon", "hackathons & competitions", "hackathons and competitions",
        "competitions", "competition", "positions of responsibility", "position of responsibility",
        "volunteering", "volunteer experience", "community involvement", "conferences", "workshops",
    ],
}


def _norm(line: str) -> str:
    return re.sub(r"\s+", " ", line.replace("\t", " ")).strip()


def _is_heading(line: str) -> str | None:
    clean = _norm(line).strip(":").strip()
    if not clean or len(clean) > 48:
        return None
    lowered = clean.lower()
    if lowered in {a for aliases in SECTION_ALIASES.values() for a in aliases}:
        for key, aliases in SECTION_ALIASES.items():
            if lowered in aliases:
                return key
    return None


def _is_bullet(line: str) -> bool:
    return bool(BULLET_PREFIX.match(line))


def _strip_bullet(line: str) -> str:
    return BULLET_PREFIX.sub("", line).strip()


def _strip_trailing_date(text: str) -> tuple[str, str, str]:
    """Remove a trailing date or date range; return (remainder, start, end)."""
    s = _norm(text)
    m = DATE_RE.search(s)
    if m and m.end() >= len(s) - 1:
        return s[: m.start()].strip(" ,|–—-"), _norm(m.group(1)), _norm(m.group(2))
    m2 = re.search(rf"(?:{_MONTH}\s*\d{{4}}|\b(?:19|20)\d{{2}}\b)\s*$", s, re.I)
    if m2:
        return s[: m2.start()].strip(" ,|–—-"), _norm(m2.group(0)), ""
    return s, "", ""


def _looks_like_entry_header(line: str, kind: str, prev_was_bullet: bool, prev_line: str) -> bool:
    if _is_bullet(line):
        return False
    clean = _norm(line)
    if not clean:
        return False
    if kind == "education":
        return bool(INSTITUTION_HINT.search(clean))
    if kind in ("experience", "projects"):
        if DATE_RE.search(clean) or "|" in clean:
            return True
        # A new entry without an explicit date/separator starts right after a
        # completed bullet (not after a wrapped bullet continuation, which
        # follows a line ending mid-sentence with a comma).
        if prev_was_bullet and clean[:1].isupper() and not prev_line.rstrip().endswith(","):
            return True
    return False


def _split_entries(lines: list[str], kind: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    prev_line = ""
    prev_was_bullet = False
    for line in lines:
        if _norm(line) == "":
            if current:
                blocks.append(current)
                current = []
            prev_line = ""
            prev_was_bullet = False
            continue
        is_bullet = _is_bullet(line)
        if current and not is_bullet and _looks_like_entry_header(line, kind, prev_was_bullet, prev_line):
            blocks.append(current)
            current = []
        current.append(line)
        prev_line = _norm(line)
        prev_was_bullet = is_bullet
    if current:
        blocks.append(current)
    return blocks


def _build_bullets(lines: list[str]) -> list[str]:
    """Collapse wrapped lines into their parent bullet."""
    bullets: list[str] = []
    for line in lines:
        text = _strip_bullet(line)
        if not text:
            continue
        if _is_bullet(line) or not bullets:
            bullets.append(text)
        else:
            bullets[-1] = f"{bullets[-1].rstrip()} {text}".strip()
    return bullets


def _extract_contacts(text: str) -> ResumeContact:
    contact = ResumeContact()
    email = EMAIL_RE.search(text)
    if email:
        contact.email = email.group(0)
    phone = PHONE_RE.search(text)
    if phone:
        contact.phone = _norm(phone.group(0))
    links: list[tuple[str, str]] = []
    linkedin = LINKEDIN_RE.search(text)
    if linkedin:
        url = linkedin.group(0)
        if not url.startswith("http"):
            url = "https://" + url
        links.append(("LinkedIn", url))
    github = GITHUB_RE.search(text)
    if github:
        url = github.group(0)
        if not url.startswith("http"):
            url = "https://" + url
        links.append(("GitHub", url))
    for url in URL_RE.findall(text):
        if "linkedin.com" in url.lower() or "github.com" in url.lower() or "mailto" in url.lower():
            continue
        full = url if url.startswith("http") else "https://" + url
        links.append(("Portfolio", full))
        break
    for label, url in links:
        contact.links.append(LinkItem(label=label, url=url))
    return contact


def _classify_link(uri: str) -> str:
    low = uri.lower()
    if "linkedin.com" in low:
        return "LinkedIn"
    if "github.com" in low:
        return "GitHub"
    if "twitter.com" in low or "//x.com" in low:
        return "Twitter"
    return "Portfolio"


def _apply_extra_links(contact: ResumeContact, uris: list[str]) -> None:
    """Fold profile-level hyperlink annotation targets into the contact block.

    Repo URLs (github.com/<user>/<repo>) belong to individual projects and are
    handled by ``_resolve_project_links``; only profile links (LinkedIn, a
    GitHub/GitLab profile, and at most one portfolio/website) land here so the
    contact line stays clean.
    """
    from urllib.parse import urlparse

    known = {link.url for link in contact.links}
    have_portfolio = any(link.label == "Portfolio" for link in contact.links)
    for raw in uris:
        uri = (raw or "").strip()
        if not uri:
            continue
        low = uri.lower()
        if low.startswith("mailto:"):
            addr = uri[len("mailto:"):].split("?")[0].strip()
            if addr and not contact.email:
                contact.email = addr
            continue
        email = EMAIL_RE.search(uri)
        if email and "://" not in uri and not uri.startswith("http"):
            if not contact.email:
                contact.email = email.group(0)
            continue
        if not uri.startswith("http"):
            uri = "https://" + uri
        if uri in known:
            continue
        host = urlparse(uri).netloc.lower()
        path = urlparse(uri).path.strip("/")
        if ("github.com" in host or "gitlab.com" in host) and path.count("/") >= 1:
            continue  # project repository — belongs to a project, not the contact line
        label = _classify_link(uri)
        if label == "Portfolio":
            if have_portfolio:
                continue
            have_portfolio = True
        known.add(uri)
        contact.links.append(LinkItem(label=label, url=uri))


def _looks_like_url(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return False
    if v.lower().startswith(("http://", "https://")):
        return True
    return bool(re.fullmatch(r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/\S*)?", v))


def _resolve_project_links(projects: list[ProjectItem], uris: list[str]) -> None:
    """Fill project links that were captured as a display label (e.g. "GitHub")
    from the resume's hyperlink annotations, matching repo URLs in order."""
    from urllib.parse import urlparse

    repos: list[str] = []
    for raw in uris or []:
        uri = (raw or "").strip()
        if not uri or "://" in uri and not uri.lower().startswith(("http://", "https://")):
            continue
        if not uri.lower().startswith("http"):
            uri = "https://" + uri
        parsed = urlparse(uri)
        host = parsed.netloc.lower()
        if ("github.com" in host or "gitlab.com" in host) and parsed.path.strip("/").count("/") >= 1:
            repos.append(uri)
    idx = 0
    for project in projects:
        if _looks_like_url(project.link):
            continue
        if idx < len(repos):
            project.link = repos[idx]
            idx += 1


def _guess_name(lines: list[str], contact: ResumeContact) -> str:
    for line in lines[:8]:
        clean = _norm(line)
        if not clean:
            continue
        if EMAIL_RE.search(clean) or URL_RE.search(clean) or PHONE_RE.search(clean):
            continue
        if len(clean.split()) <= 5 and len(clean) <= 50 and re.search(r"[A-Za-z]", clean):
            return clean
    return ""


def _parse_experience_block(block: list[str]) -> ExperienceItem:
    item = ExperienceItem()
    header, item.start, item.end = _strip_trailing_date(_norm(block[0]))
    body = block[1:]
    if body and not _is_bullet(body[0]):
        nxt = _norm(body[0])
        remainder, n_start, n_end = _strip_trailing_date(nxt)
        if remainder == "" and (n_start or n_end):
            if not item.start:
                item.start, item.end = n_start, n_end
            body = body[1:]
        else:
            item.company = nxt
            body = body[1:]
    if item.company:
        item.role = header
    else:
        parts = [p.strip() for p in re.split(r"\s+[|@]\s+|\s+[–—]\s+|\s+-\s+|,", header) if p.strip()]
        item.role = parts[0] if parts else header
        if len(parts) > 1:
            item.company = parts[1]
    item.bullets = _build_bullets(body)
    return item


def _parse_education_block(block: list[str]) -> EducationItem:
    item = EducationItem()
    header, item.start, item.end = _strip_trailing_date(_norm(block[0]))
    parts = [p.strip(" ,") for p in re.split(r"\s+[—–]\s+|\s+\|\s+", header) if p.strip()]
    institution = parts[0] if parts else header
    degree = parts[1] if len(parts) > 1 else ""
    body = block[1:]
    if body:
        first = _norm(body[0])
        remainder, f_start, f_end = _strip_trailing_date(first)
        if _is_bullet(body[0]):
            pass
        elif remainder == "" and (f_start or f_end):
            if not item.start:
                item.start, item.end = f_start, f_end
            body = body[1:]
        elif DEGREE_HINT.search(first):
            if not degree:
                degree = remainder or first
            if not item.start:
                item.start, item.end = f_start, f_end
            body = body[1:]
    item.institution = institution
    item.degree = degree
    item.details = _build_bullets(body)
    return item


def _is_link_segment(segment: str) -> bool:
    low = segment.lower().strip()
    if URL_RE.search(segment):
        return True
    if "github" in low or "gitlab" in low or "linkedin" in low:
        return True
    if "demo" in low or low in {"website", "link", "repo", "repository", "live", "live demo", "code"}:
        return True
    return False


def _parse_project_block(block: list[str]) -> ProjectItem:
    item = ProjectItem()
    header, _, _ = _strip_trailing_date(_norm(block[0]))
    link = URL_RE.search(header)
    if link:
        item.link = link.group(0)
        header = _norm(header[: link.start()])
    tech_match = re.search(r"[\(\[\{]([^)\]\}]*)[\)\]\}]", header)
    if tech_match:
        item.tech = [t.strip() for t in re.split(r"[,/|]", tech_match.group(1)) if t.strip()]
        header = _norm(header[: tech_match.start()])
    if "|" in header:
        segments = [s.strip() for s in header.split("|") if s.strip()]
        item.name = segments[0] if segments else header
        tech: list[str] = []
        for seg in segments[1:]:
            if _is_link_segment(seg):
                if not item.link:
                    item.link = seg
            else:
                tech += [t.strip() for t in re.split(r"[,/]", seg) if t.strip()]
        if not item.tech:
            item.tech = tech
    else:
        dash_parts = re.split(r"\s+[–—-]\s+", header)
        if len(dash_parts) == 2 and len(dash_parts[1].split()) <= 8 and not item.tech:
            item.name = dash_parts[0].strip()
            item.tech = [t.strip() for t in re.split(r"[,/]", dash_parts[1]) if t.strip()]
        else:
            item.name = header
    item.bullets = _build_bullets(block[1:])
    return item


def _parse_skills(lines: list[str]) -> list[SkillGroup]:
    groups: list[SkillGroup] = []
    for line in lines:
        clean = _strip_bullet(_norm(line))
        if not clean:
            continue
        if ":" in clean:
            category, rest = clean.split(":", 1)
            items = [i.strip() for i in re.split(r"[,;|/]", rest) if i.strip()]
            if items:
                groups.append(SkillGroup(category=category.strip()[:60] or "Skills", items=items))
                continue
        items = [i.strip() for i in re.split(r"[,;|/•]", clean) if i.strip()]
        if items:
            groups.append(SkillGroup(category="Skills", items=items))
    return groups


def structure_text(text: str, contact_links: list[str] | None = None) -> tuple[ResumeContent, float]:
    lines = text.splitlines()
    contact = _extract_contacts(text)
    contact.name = _guess_name(lines, contact)
    if contact_links:
        _apply_extra_links(contact, contact_links)

    current_section: str | None = None
    buckets: dict[str, list[str]] = {k: [] for k in SECTION_ALIASES}
    preamble: list[str] = []

    for line in lines:
        if _norm(line) == "":
            if current_section:
                buckets[current_section].append("")
            elif preamble:
                preamble.append("")
            continue
        heading = _is_heading(line)
        if heading:
            current_section = heading
            continue
        if current_section:
            buckets[current_section].append(line)
        else:
            preamble.append(line)

    content = ResumeContent(contact=contact)

    has_summary_section = bool([x for x in buckets["summary"] if _norm(x)])
    if has_summary_section:
        summary_text = " ".join(_norm(x) for x in buckets["summary"] if _norm(x))
    else:
        # Fall back to pre-section prose, dropping name/contact lines.
        cleaned: list[str] = []
        for x in preamble:
            n = _norm(x)
            if not n or n == contact.name:
                continue
            if EMAIL_RE.search(n) or PHONE_RE.search(n) or URL_RE.search(n):
                continue
            if LINKEDIN_RE.search(n) or GITHUB_RE.search(n):
                continue
            if len([p for p in n.split("|") if p.strip()]) >= 3:
                continue
            cleaned.append(n)
        summary_text = " ".join(cleaned)
    if summary_text and len(summary_text) > 40:
        content.summary = summary_text[:1500]

    for block in _split_entries(buckets["experience"], "experience"):
        item = _parse_experience_block(block)
        if item.role or item.company or item.bullets:
            content.experience.append(item)

    for block in _split_entries(buckets["projects"], "projects"):
        item = _parse_project_block(block)
        if item.name or item.bullets:
            content.projects.append(item)
    if contact_links:
        _resolve_project_links(content.projects, contact_links)

    for block in _split_entries(buckets["education"], "education"):
        item = _parse_education_block(block)
        if item.institution or item.degree or item.details:
            content.education.append(item)

    content.skills = _parse_skills(buckets["skills"])
    content.certifications = [_strip_bullet(_norm(x)) for x in buckets["certifications"] if _norm(x)]
    content.achievements = [_strip_bullet(_norm(x)) for x in buckets["achievements"] if _norm(x)]

    filled = sum(
        [
            bool(contact.name),
            bool(contact.email),
            bool(content.summary),
            bool(content.experience),
            bool(content.projects),
            bool(content.education),
            bool(content.skills),
        ]
    )
    confidence = round(filled / 7, 2)
    return content, confidence
