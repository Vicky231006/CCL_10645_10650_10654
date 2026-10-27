"""FastAPI dependencies: authentication, CSRF, and ownership checks."""
from __future__ import annotations

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import csrf_matches, decode_access_token
from app.models import User


def _extract_token(request: Request) -> tuple[str | None, bool]:
    """Return (token, used_bearer)."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip(), True
    return request.cookies.get(settings.cookie_name), False


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token, _ = _extract_token(request)
    if not token:
        raise UnauthorizedError("Authentication required.")
    subject = decode_access_token(token)
    if not subject:
        raise UnauthorizedError("Invalid or expired session.")
    user = db.get(User, subject)
    if not user or not user.is_active:
        raise UnauthorizedError("Account not found or inactive.")
    return user


def require_csrf(
    request: Request,
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> None:
    """CSRF double-submit check for cookie-authenticated state-changing requests.

    Bearer-token requests (API clients) are exempt because the token is not ambient.
    """
    _, used_bearer = _extract_token(request)
    if used_bearer:
        return
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    if not csrf_matches(cookie_token, x_csrf_token):
        raise ForbiddenError("CSRF validation failed. Refresh the page and try again.", code="csrf_failed")
