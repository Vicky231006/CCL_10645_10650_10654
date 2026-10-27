"""Pytest fixtures for the Resumo backend."""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Configure a deterministic test environment BEFORE importing the app.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_resumo.db")
os.environ.setdefault("JOB_RUNNER", "inline")
os.environ.setdefault("LLM_PROVIDER", "none")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("LOCAL_STORAGE_DIR", "./test_storage")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.db import Base, engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    db_path = Path("test_resumo.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    from app.core.rate_limit import reset_rate_limits

    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        c.get("/api/v1/auth/csrf")
        yield c


@pytest.fixture()
def auth(client):
    """Return (headers_with_csrf, user_dict) for a freshly signed-up user."""

    def _signup(email: str = "user@example.com", password: str = "password123"):
        r = client.post("/api/v1/auth/signup", json={"email": email, "password": password, "full_name": "Test User"})
        assert r.status_code == 200, r.text
        body = r.json()
        return {"X-CSRF-Token": body["csrf_token"]}, body["user"]

    return _signup
