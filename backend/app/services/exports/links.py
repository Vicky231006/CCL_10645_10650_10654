"""Helpers for rendering friendly, clickable links in resume exports."""
from __future__ import annotations

from urllib.parse import urlparse

_KNOWN = (
    ("linkedin.com", "LinkedIn"),
    ("github.com", "GitHub"),
    ("gitlab.com", "GitLab"),
    ("bitbucket.org", "Bitbucket"),
    ("twitter.com", "Twitter"),
    ("x.com", "X"),
    ("behance.net", "Behance"),
    ("dribbble.com", "Dribbble"),
    ("medium.com", "Medium"),
    ("youtube.com", "YouTube"),
    ("kaggle.com", "Kaggle"),
)


import re

_DOMAIN_RE = re.compile(r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/\S*)?")


def ensure_url(url: str) -> str:
    """Return a URL that already carries a scheme.

    Adds ``https://`` to bare domains, but returns "" for values that are not
    URLs at all (e.g. a captured display label like "GitHub"), so callers never
    emit a broken ``https://GitHub`` link.
    """
    u = (url or "").strip()
    if not u:
        return ""
    if u.lower().startswith(("http://", "https://", "mailto:", "tel:")):
        return u
    if _DOMAIN_RE.fullmatch(u):
        return "https://" + u
    return ""


def mailto(email: str) -> str:
    e = (email or "").strip()
    if not e:
        return ""
    if e.lower().startswith("mailto:"):
        return e
    return "mailto:" + e


def link_label(url: str, fallback: str = "Link") -> str:
    """A short, human label for a link (e.g. GitHub, LinkedIn, or the host name)."""
    u = (url or "").strip().lower()
    if not u:
        return fallback
    if u.startswith("mailto:"):
        return "Email"
    for needle, label in _KNOWN:
        if needle in u:
            return label
    host = urlparse(ensure_url(u)).netloc
    host = host[4:] if host.startswith("www.") else host
    return host or fallback
