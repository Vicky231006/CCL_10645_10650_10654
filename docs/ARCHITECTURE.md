# Resumo — Technical Architecture

## Overview
Resumo is a modular monolith. One FastAPI service owns all domain modules and one Postgres (or SQLite
for local dev) database. The React SPA talks to a versioned REST API under `/api/v1`.

```
Browser (React SPA)
   │  HTTPS, httpOnly session cookie + CSRF double-submit
   ▼
FastAPI (modular monolith)  ──►  PostgreSQL / SQLite
   │        │        │
   │        │        └──► Storage adapter (S3 | local filesystem)
   │        └────────────► LLM provider (Ollama | OpenAI-compatible | Null)
   └─────────────────────► Job runner (in-process pool | SQS + worker)
```

## Backend module layout
```
backend/app/
  main.py                 app factory, middleware, router mounting
  core/
    config.py             pydantic-settings, env-driven
    db.py                 engine/session, Base, init
    security.py           password hashing, JWT, CSRF
    deps.py               auth dependencies, ownership guards
    errors.py             typed error envelope + handlers
    logging.py            structured logging (no PII)
    rate_limit.py         in-memory token bucket
  models/                 SQLAlchemy 2.0 ORM models (UUID PKs)
  schemas/                Pydantic v2 request/response models
  api/v1/                 routers, one per domain
  services/
    parsers/              parser registry (pdf, docx, doc, txt, md, rtf, odt, tex, html, images)
    quality/              deterministic resume scoring engine
    matching/             keyword extraction + semantic match scoring
    ai/                   provider abstraction, prompt templates, truth-check pipeline
    exports/              PDF (reportlab), DOCX (python-docx), LaTeX, plain text
    storage.py            S3 / local adapter
    jobs.py               background job runner abstraction
    research.py           source-grounded company research (fetch + cite)
    seed.py               labelled sample data
```

## Key decisions and rationale
1. **Sync SQLAlchemy + `def` endpoints.** FastAPI runs blocking endpoints in a threadpool. This keeps
   ORM code simple and reliable across Postgres (prod) and SQLite (dev/test) with one code path.
2. **Portable identifiers.** UUID4 string primary keys everywhere; non-guessable, safe for URLs.
3. **Auth = httpOnly cookie session (JWT) + CSRF double-submit token.** Tokens are never placed in
   `localStorage`. Bearer header is also accepted for API clients/tests.
4. **Password hashing without fragile deps.** PBKDF2-HMAC-SHA256 (stdlib `hashlib`), per-user salt,
   210k iterations. Avoids the `bcrypt`/`passlib` Python 3.13 build issues.
5. **Truth-preserving AI pipeline.** `facts → generate → verify → review → apply`. Verification rejects
   suggestions containing numbers/dates/entities absent from the source facts; everything is a
   reviewable suggestion the user must approve.
6. **Deterministic-first scoring.** Quality/match scores are computed from rules; AI may add qualitative
   commentary that is clearly labelled. Methodology is always disclosed.
7. **PDF-editor strategy.** Editing arbitrary PDF bytes in-browser is brittle and ATS-hostile. The
   strategy is documented in `docs/PDF_EDITOR_STRATEGY.md`: import → parse → structured edit → re-export.

## Data flow: upload → analyze → tailor → export
1. `POST /api/v1/resumes/upload` validates signature/size, stores original, creates `ResumeDocument`.
2. A background parse job fills `ResumeSection`/structured JSON; parsing confidence is recorded.
3. User corrects structured content via `PATCH /resumes/{id}`. Original file is retained.
4. `POST /resumes/{id}/analyze` runs the deterministic engine (and optional AI commentary).
5. `POST /matches` compares a resume version against a saved job description.
6. `POST /exports` renders PDF/DOCX/LaTeX/TXT from the current structured resume.
7. `POST /tailor/suggestions` + `/tailor/apply` produce reviewed, approved edits.

## Security posture
- Upload allowlist + magic-byte verification; size/page caps; object keys generated server-side.
- No execution of uploaded LaTeX/macros/HTML; parser inputs are size-bounded.
- SSRF guard for user-supplied URLs (block private ranges, scheme allowlist).
- Ownership check on every user-scoped lookup (prevents IDOR).
- CORS restricted to configured origins; security headers on every response; audit log.
- Prompt-injection defence: document/JD/web content is wrapped as untrusted data, never as instructions.

## Deployment (AWS, documented not provisioned)
EC2 (FastAPI + worker via systemd or Docker) · RDS Postgres · private S3 · IAM least privilege ·
SSM Parameter Store for secrets · CloudWatch logs/alarms · CloudFront for TLS and edge caching.
No infrastructure is created by this repository without explicit authorisation.

> Detailed multi-tier AWS cloud topology, network segmentation, Mermaid flowcharts, and security matrices are documented in [docs/AWS_ARCHITECTURE.md](file:///c:/Users/Vicky/Desktop/CCL_MINI_deepseek/docs/AWS_ARCHITECTURE.md). For step-by-step console instructions, see [docs/DEPLOYMENT.md](file:///c:/Users/Vicky/Desktop/CCL_MINI_deepseek/docs/DEPLOYMENT.md).

