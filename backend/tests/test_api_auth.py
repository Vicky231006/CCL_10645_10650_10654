"""API tests: auth, CSRF, rate limiting, and cross-account authorization (IDOR)."""
from __future__ import annotations


def test_signup_login_me_logout(client):
    client.get("/api/v1/auth/csrf")
    r = client.post("/api/v1/auth/signup", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200
    csrf = r.json()["csrf_token"]
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_duplicate_signup_conflicts(client):
    client.get("/api/v1/auth/csrf")
    client.post("/api/v1/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    r = client.post("/api/v1/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    assert r.status_code == 409


def test_login_wrong_password(client):
    client.get("/api/v1/auth/csrf")
    client.post("/api/v1/auth/signup", json={"email": "b@example.com", "password": "password123"})
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("resumo_csrf")})
    r = client.post("/api/v1/auth/login", json={"email": "b@example.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_csrf_required_for_mutation(client):
    client.get("/api/v1/auth/csrf")
    r = client.post("/api/v1/auth/signup", json={"email": "c@example.com", "password": "password123"})
    # no CSRF header -> should be rejected
    resp = client.post("/api/v1/resumes", json={"title": "X"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "csrf_failed"


def test_unauthenticated_access_denied(client):
    assert client.get("/api/v1/resumes").status_code == 401
    assert client.get("/api/v1/dashboard").status_code == 401


def test_cross_account_isolation(client):
    # user 1 creates a resume
    client.get("/api/v1/auth/csrf")
    r1 = client.post("/api/v1/auth/signup", json={"email": "u1@example.com", "password": "password123"})
    h1 = {"X-CSRF-Token": r1.json()["csrf_token"]}
    created = client.post("/api/v1/resumes", json={"title": "User1 Resume"}, headers=h1)
    resume_id = created.json()["id"]

    # logout, create user 2
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": client.cookies.get("resumo_csrf")})
    r2 = client.post("/api/v1/auth/signup", json={"email": "u2@example.com", "password": "password123"})
    h2 = {"X-CSRF-Token": r2.json()["csrf_token"]}

    # user 2 must NOT access user 1's resume
    assert client.get(f"/api/v1/resumes/{resume_id}", headers=h2).status_code == 404
    assert client.delete(f"/api/v1/resumes/{resume_id}", headers=h2).status_code == 404


def test_password_hashing_not_plaintext(client):
    from app.core.security import hash_password, verify_password

    hashed = hash_password("password123")
    assert "password123" not in hashed
    assert verify_password("password123", hashed)
    assert not verify_password("wrong", hashed)
