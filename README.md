# Resumo

> AI-assisted **resume intelligence, job-matching and career-preparation** platform.
> Resumo tells you exactly what your resume says, what a job actually requires,
> and what to build next — with transparent, explainable scoring and no invented
> facts. It is advisory tooling: scores are guidance, **not** employer ATS scores
> or hiring predictions.

---

## What it does

1. **Ingest** — upload a resume in nearly any format (PDF, DOCX, DOC, TXT, Markdown,
   RTF, ODT, LaTeX, HTML, or a scanned image) or build one from a clean template.
   Every format is normalised into one editable structured model.
2. **Diagnose** — deterministic quality analysis across six weighted categories,
   with the exact excerpt, an explanation, and a specific suggested fix for each
   finding. Optional AI commentary is added *separately* and never changes the
   deterministic score.
3. **Match** — paste a real job description; Resumo extracts required vs preferred
   requirements and shows which are **evidenced**, **weak**, or **genuinely missing**,
   with the evidence location in your resume.
4. **Close the gap** — a readiness-scored roadmap whose every milestone cites the
   job requirement behind it, plus achievable project briefs with acceptance
   criteria, and curated learning resources.
5. **Build evidence** — record real project evidence, generate README/case-study/bio
   drafts grounded only in your own inputs, publish a portfolio page, and export
   job-specific resumes as PDF, DOCX, LaTeX, or text.
6. **Track** — an application board that keeps each role next to the resume, match
   report and roadmap behind it.

## Honesty by design

- **Truth preservation**: AI suggestions pass a verifier (`services/ai/truth.py`)
  that blocks newly introduced numbers, dates, technologies and named entities.
  Unverified suggestions cannot be applied.
- **Deterministic first**: parsing, scoring, matching and export work with **no AI
  at all**. AI is opt-in and clearly labelled.
- **No scraping of private data**: company insights are grounded in sources *you*
  provide, with citations. Demo job listings are explicitly labelled as samples.
- **Explainable scores**: the methodology string is returned alongside every score.

---

## Tech stack

| Layer | Choices |
|-------|---------|
| API | FastAPI 0.115, Pydantic v2, SQLAlchemy 2.0, Alembic, Uvicorn |
| Auth | httpOnly JWT cookie + CSRF double-submit (PBKDF2-HMAC-SHA256, stdlib) |
| Parsing | pypdf, pdfminer.six, python-docx, striprtf, odfpy, beautifulsoup4/lxml, Pillow |
| Export | reportlab (PDF), python-docx (DOCX), LaTeX (Jake's-template inspired), text |
| AI (optional) | Provider abstraction: Ollama, OpenAI-compatible, or Null |
| Web | React 18, TypeScript, Vite, React Router, TanStack Query, Tailwind, lucide-react |
| Tests | pytest (backend), Vitest + Testing Library (frontend) |
| Deploy | Docker, docker compose, nginx; AWS guide in `docs/DEPLOYMENT.md` |

---

## Repository layout

```
backend/
  app/
    core/        config, db, security, errors, logging, rate limiting, deps
    models/      SQLAlchemy ORM (users, resumes, jobs, career)
    schemas/     Pydantic request/response models
    services/    parsers, quality, matching, ai, exports, career, storage, seed
    api/v1/      routers: auth, profile, dashboard, resumes, jobs, discovery,
                 tailor, career, company, applications, health
    main.py      app factory (middleware, routers, lifespan)
  migrations/    Alembic environment + initial schema revision
  scripts/       seed_demo.py — populate a fully-featured demo account
  tests/         pytest suite (parsers, quality, matching, API auth, workflow)
frontend/
  src/
    lib/         api client, auth context, types, utils
    components/  design-system primitives, Score, Layout, ResumePreview
    pages/       public/* and app/*
    tests/       Vitest setup + component tests
docs/            IMPLEMENTATION_PLAN, ARCHITECTURE, COMPETITIVE_ANALYSIS,
                 PDF_EDITOR_STRATEGY, DEPLOYMENT
docker-compose.yml, .env.example
```

---

## Running locally (without Docker)

**Backend** (Python 3.13; SQLite by default):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/api/docs
```

Copy `backend/.env.example` to `backend/.env` to change settings (storage, AI,
database). No secrets are required for the default local setup.

**Frontend** (Node 22):

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173  (proxies /api -> localhost:8000)
```

### Optional local AI (Ollama)

```bash
ollama pull qwen2.5:1.5b
# .env: LLM_PROVIDER=ollama, OLLAMA_BASE_URL=http://localhost:11434
```

Deterministic features work without this. When the provider is unreachable the
UI says so and keeps working.

### One-command launcher + seeded demo account

```powershell
.\start.ps1            # starts the API + web app together, waits for both
.\start.ps1 -SeedDemo  # ...and first seeds a fully-populated demo account
.\start.ps1 -Stop      # stop both services
```

The demo account is built from the bundled resume by
`backend/scripts/seed_demo.py`, which drives the real API end-to-end so every
screen is populated: a parsed resume, quality analysis, three job descriptions
with match reports, saved jobs, two career roadmaps (with milestones done /
in-progress), project plans with evidence and generated assets, resume
tailoring suggestions (accepted + pending), a published portfolio, five
applications across the pipeline, a completed profile and sample company
research.

```
email:    demo@resumo.app
password: demo1234
```

Run it directly any time (it resets only the demo account):

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\seed_demo.py
```

---

## Running with Docker (production-shaped)

```bash
cp .env.example .env      # set SECRET_KEY (and POSTGRES_PASSWORD) at minimum
docker compose up --build
# Frontend: http://localhost:8080     API docs: http://localhost:8080/api/docs
```

This starts Postgres, runs Alembic migrations on the API container
(`RUN_MIGRATIONS=1`), and serves the built SPA through nginx with `/api`
proxied to the backend.

---

## Testing

**Backend**

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Covers format detection/parsing, structuring, the quality engine, the matching
engine, auth/CSRF flows, and a full end-to-end API workflow
(upload → analyse → match → roadmap → tailor → application).

**Frontend**

```bash
cd frontend
npm run lint      # tsc --noEmit
npm test          # vitest
npm run build     # type-check + production bundle
```

---

## API surface (selected)

| Method & path | Purpose |
|---------------|---------|
| `POST /api/v1/auth/signup`, `/login`, `/logout`, `GET /auth/me` | Session auth |
| `GET /api/v1/auth/csrf` | Bootstrap CSRF cookie |
| `GET/PATCH /api/v1/profile` | Profile & targets |
| `GET /api/v1/dashboard` | Aggregated workspace summary |
| `POST /api/v1/resumes` / `/upload` | Create (builder) / ingest |
| `GET/PATCH/DELETE /api/v1/resumes/{id}` | Read / edit / delete |
| `POST /api/v1/resumes/{id}/analyze`, `GET .../analyses` | Quality analysis |
| `POST /api/v1/resumes/{id}/export` | PDF/DOCX/LaTeX/TXT export |
| `POST/GET /api/v1/jobs` | Job descriptions + parsed requirements |
| `POST /api/v1/jobs/match`, `GET /matches` | Evidence-based matching |
| `GET /api/v1/listings`, `/recommendations` | Sample listings & ranked fits |
| `POST /api/v1/saved-jobs`, `GET /saved-jobs` | Saved roles |
| `POST /api/v1/roadmaps`, `GET /roadmaps/{id}`, `PATCH /milestones/{id}` | Career plan |
| `POST /api/v1/projects`, `.../evidence` | Project briefs & evidence |
| `GET/POST/PATCH /api/v1/portfolio` | Portfolio page management |
| `POST /api/v1/assets/generate` | Grounded drafts (README, case study, bio…) |
| `POST /api/v1/tailor/suggestions`, `/apply` | Truth-checked rewriting |
| `POST/GET /api/v1/company` | Company research with citations |
| `POST/GET/PATCH/DELETE /api/v1/applications` | Application tracker |
| `GET /api/v1/health`, `/ready`, `/meta/formats`, `/meta/ai-status` | Ops & meta |

Full interactive schema at `/api/docs`.

---

## Design decisions worth knowing

- **One structured resume model** for every format keeps analysis, matching,
  tailoring and export consistent.
- **Payments and verification claims are deliberately out of scope.** The product
  promises an honest assessment, not a "guaranteed ATS pass".
- **CSRF & cookies**: `POST /auth/signup` and `/login` are exempt from CSRF;
  `GET /auth/csrf` bootstraps the token, and signup rotates it (clients must use
  the returned `csrf_token`). Bearer auth is also accepted (CSRF-exempt) for API
  clients.
- **Scoring ranges**: resume quality is `0–10`; job alignment is `0–100`.
- **Storage is abstracted** (`local` | `s3`) so dev needs no cloud account.
- **Jobs runner** is pluggable (`inline`/`thread`/`sqs`) for future async work.

## Limitations / not production-hardened

- Email verification and password reset are modelled but not wired to a mail
  provider; treat new accounts as unverified.
- Rate limiting is in-memory (single process); use a shared store behind more
  than one worker.
- Company "research" is a structured synthesis of user-provided sources, not a
  live crawler.
- The scanned-image parser is best-effort and reports low confidence rather than
  guessing.
- Before real production use, obtain legal/security review, add a real email
  provider, externalise secrets to a manager, and add WAF + backups.

See `docs/DEPLOYMENT.md` for the AWS deployment guide.
