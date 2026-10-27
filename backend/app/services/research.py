"""Source-grounded company research.

Only fetches URLs the user explicitly supplies (or openly discoverable official pages),
with SSRF protection and size/time limits. Never scrapes restricted profiles or bypasses
login/CAPTCHA. Every output includes source links and retrieval metadata.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.logging import get_logger

logger = get_logger("resumo.research")

MAX_BYTES = 400_000
TIMEOUT = 15
ALLOWED_SCHEMES = {"http", "https"}


class UnsafeUrlError(ValueError):
    pass


def _is_public_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return False
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


def validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeUrlError("Only http and https URLs are allowed.")
    if not parsed.hostname:
        raise UnsafeUrlError("URL has no hostname.")
    if not _is_public_host(parsed.hostname):
        raise UnsafeUrlError("URL resolves to a private or non-public address (blocked).")
    return url.strip()


@dataclass
class Source:
    url: str
    label: str
    text: str
    retrieved_at: str
    source_type: str = "public"
    excerpt: str = ""
    error: str | None = None


@dataclass
class ResearchResult:
    summary: str
    themes: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    confidence: str = "inference"


def _clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def fetch_source(url: str) -> Source:
    now = datetime.now(timezone.utc).isoformat()
    try:
        safe = validate_url(url)
    except UnsafeUrlError as exc:
        return Source(url=url, label=url, text="", retrieved_at=now, error=str(exc))
    try:
        with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent": "ResumoResearchBot/1.0"}) as client:
            resp = client.get(safe)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            raw = resp.content[:MAX_BYTES]
        if "html" in content_type:
            text = _clean_text(raw.decode(resp.encoding or "utf-8", errors="replace"))
        else:
            text = raw.decode("utf-8", errors="replace")
        label = urlparse(safe).netloc
        return Source(url=safe, label=label, text=text[:12000], retrieved_at=now, excerpt=text[:400])
    except httpx.HTTPError as exc:
        logger.info("fetch failed", extra={"extra_fields": {"url": url, "error": str(exc)}})
        return Source(url=url, label=url, text="", retrieved_at=now, error=f"Fetch failed: {exc}")


KNOWN_SOURCE_TYPES = {
    "github.com": "github",
    "engineering": "engineering_blog",
    "careers": "careers_page",
    "blog": "blog",
    "linkedin.com": "professional_profile",
}


def classify_source(url: str) -> str:
    low = url.lower()
    for key, value in KNOWN_SOURCE_TYPES.items():
        if key in low:
            return value
    return "public"
