# Resumo — Implementation Plan

Status legend: `[x]` done & verified, `[~]` partially done, `[ ]` not started / blocked.

## 1. Existing repository state
- The repository contained only `PROMPT.md`. No application code, no git history, no package manifests.
- Therefore Resumo is a greenfield build. No existing working functionality was overwritten.

## 2. Environment constraints (verified)
- Windows 10/11, PowerShell 5.1.
- Node `v22.19.0`, npm `10.9.3`.
- Python `3.13.7` (`py` launcher present).
- Git `2.51.0` present, but the folder is **not** a git repo.
- Docker CLI `29.6.1` present, **Docker daemon not running** → Postgres/RDS emulation via docker-compose
  cannot be exercised here. Local development therefore defaults to **SQLite** with a storage adapter
  that writes to the local filesystem instead of S3.
- Ollama `0.40.4` is running on `http://localhost:11434` with model **`qwen2.5:1.5b`** available.

## 3. Architecture decision summary
- **Modular monolith** backend (FastAPI, sync SQLAlchemy 2.0) + SPA frontend (React/TS/Vite).
- Durable database portability: `DATABASE_URL` selects PostgreSQL (prod/RDS) or SQLite (local/test).
- Storage portability: `STORAGE_BACKEND` selects `s3` (prod) or `local` (dev/test).
- Background work: a pluggable `JobRunner` — in-process thread pool for dev, SQS + worker for prod.
- AI: provider-agnostic `LLMProvider` interface. `OllamaProvider` (default, local qwen2.5:1.5b) and
  a deterministic `NullProvider`. All AI features degrade to deterministic results when no provider is
  configured, and clearly signal that AI text was not generated.
- Every AI-generated artifact is **validated against source facts** before it is stored or shown.

Full details: `docs/ARCHITECTURE.md`.

## 4. Phases
Phase 1 Foundation — `[x]` design tokens, app shell, DB, migrations, health, auth, errors, logging.
Phase 2 Resume workflow — `[x]` multi-format upload, parser registry, structured model, quality engine, persistence.
Phase 3 Job matching — `[x]` JD parsing, keyword table, transparent match scoring, saved JDs + history.
Phase 4 Resume builder — `[x]` Jake's-template rendition, live preview, editing, tailoring, PDF/DOCX/LaTeX/TXT export.
Phase 5 Career development — `[x]` gap reports, resources, project briefs, milestones, portfolio assets.
Phase 6 Discovery & company intel — `[~]` adapter architecture + labelled seed data + application tracker + URL-grounded company research (no unauthorised scraping).
Phase 7 Production hardening — `[~]` accessibility, security headers, tests, Docker, AWS docs.

## 5. Verified deliverables
See `README.md` ("What is implemented / verified") and the final report. Tests are run with the exact
commands in `README.md`; results are recorded in `docs/TEST_RESULTS.md`.
