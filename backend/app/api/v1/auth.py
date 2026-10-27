"""Authentication routes: signup, login, logout, current user."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user, require_csrf
from app.core.errors import ConflictError, UnauthorizedError
from app.core.rate_limit import check_rate_limit
from app.core.security import create_access_token, hash_password, new_csrf_token, verify_password
from app.models import AuditEvent, Profile, User
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookies(response: Response, token: str, csrf: str) -> None:
    response.set_cookie(
        settings.cookie_name, token, httponly=True, secure=settings.cookie_secure,
        samesite="lax", max_age=settings.access_token_ttl_minutes * 60,
        domain=settings.cookie_domain or None, path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name, csrf, httponly=False, secure=settings.cookie_secure,
        samesite="lax", max_age=settings.access_token_ttl_minutes * 60,
        domain=settings.cookie_domain or None, path="/",
    )


@router.get("/csrf")
def csrf(response: Response) -> dict:
    """Bootstrap endpoint: issues a CSRF cookie for double-submit protection."""
    token = new_csrf_token()
    response.set_cookie(
        settings.csrf_cookie_name, token, httponly=False, secure=settings.cookie_secure,
        samesite="lax", domain=settings.cookie_domain or None, path="/",
    )
    return {"csrf_token": token}


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    check_rate_limit(f"signup:{request.client.host if request.client else 'anon'}", limit=10, window_seconds=300)
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise ConflictError("An account with this email already exists.")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), full_name=payload.full_name)
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id))
    db.add(AuditEvent(user_id=user.id, action="user.signup", target_type="user", target_id=user.id))
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    csrf = new_csrf_token()
    _set_session_cookies(response, token, csrf)
    return AuthResponse(user=UserOut.model_validate(user), csrf_token=csrf)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    ip = request.client.host if request.client else "anon"
    check_rate_limit(f"login:{ip}", limit=10, window_seconds=300)
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        check_rate_limit(f"loginfail:{ip}", limit=5, window_seconds=300)
        raise UnauthorizedError("Invalid email or password.")
    token = create_access_token(user.id)
    csrf = new_csrf_token()
    _set_session_cookies(response, token, csrf)
    db.add(AuditEvent(user_id=user.id, action="user.login", target_type="user", target_id=user.id))
    db.commit()
    return AuthResponse(user=UserOut.model_validate(user), csrf_token=csrf)


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(response: Response) -> dict:
    response.delete_cookie(settings.cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
    return {"message": "Logged out."}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
