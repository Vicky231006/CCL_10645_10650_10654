# Resumo — End-to-End Test Report

Date: 2026-10-18
Environment: Windows 10/11, PowerShell 5.1 · Python 3.13.7 · Node v22.19.0 · npm 10.9.3
App: `CCL_MINI_deepseek`
Test inputs (representative professional technical resumes):
- `Candidate_Profile_A.pdf` (multi-project systems resume, ~99 KB)
- `Candidate_Profile_B.pdf` (multi-education full-stack resume, ~107 KB)

All commands below are reproducible from the repository.

---

## 1. Summary of results

| Suite | Command | Result |
| --- | --- | --- |
| Backend unit + integration | `cd backend ; .\.venv\Scripts\python.exe -m pytest -q` | **46 passed** |
| └ of which parser tests | `pytest tests/test_parsers.py -q` | 16 passed |
| └ of which real-resume E2E tests | `pytest tests/test_e2e_real_resumes.py -q` | 4 passed |
| Frontend unit tests | `cd frontend ; npm test` | **8 passed** |
| Frontend typecheck + build | `npm run build` | **success** (tsc + vite) |

Every test listed passed on the final run. No test was skipped (the test PDFs were present).

---

## 2. Bugs found and fixed

The professional technical resumes exposed several defects in the heuristic PDF → structured-resume
pipeline (`backend/app/services/parsers/`). All were fixed and locked in with
regression tests.

### 2.1 Multi-entry sections collapsed into a single entry
**Symptom:** every project/education/experience entry was merged into one object
(e.g. Profile A's 3 projects and 2 education entries became 1 each; a project bullet
"`ML inference, and hospital infrastructure.`" became a bogus project *name*).
**Cause:** section splitting relied only on blank lines, which resume PDFs rarely contain.
**Fix:** added `_split_entries()` which detects new entries using strong signals —
a date range, a `|` tech separator, an institution keyword, or the transition from a
completed bullet to a new title-case line. Added `_looks_like_entry_header()`.
(`structuring.py`)

### 2.2 Contact / name line leaked into the summary
**Symptom:** the top contact line (`+91 … | email | LinkedIn | GitHub`) was stored as
the resume summary for resumes with no explicit "Summary" heading.
**Cause:** the preamble fallback joined every pre-section line.
**Fix:** the preamble is now filtered — name line, lines containing email/phone/URL/
LinkedIn/GitHub, and pipe-delimited contact rows are excluded. (`structuring.py`)

### 2.3 Non-heading sections absorbed into the previous section
**Symptom:** Profile A's "Hackathons & Competitions" block was dumped into Experience bullets.
**Fix:** extended `SECTION_ALIASES` with hackathons/competitions, positions of
responsibility, volunteering, conferences, workshops, etc. (`structuring.py`)

### 2.4 Company / role parsing errors
**Symptom:** Profile B's company parsed as `"Incoming"` (the tail of the role line) and the
real employer line was lost; the employer/location lines ran into the header.
**Cause:** the header was split on separators before checking the following line.
**Fix:** if the line after the header is a non-bullet, non-date line it is treated as the
company/organisation and the whole header becomes the role; date-only lines are consumed
as the start/end instead of becoming bullets. (`_parse_experience_block`)

### 2.5 Education dates lost / degrees merged
**Symptom:** education dates empty; institution name glued to the date
(`"...College of EngineeringSep. 2024"`).
**Fix:** added `_strip_trailing_date()` (ranges *and* single month/year), a
degree/institution split, and per-entry date capture from the degree line.
(`_parse_education_block`)

### 2.6 Wrapped bullet lines split into separate bullets
**Symptom:** a bullet wrapped across two PDF lines became two bullets; worse, when the
second line started with an acronym (`ML inference…`, `PDF merging…`) it was treated as a
**new project entry**.
**Fix:** added `_build_bullets()` to merge wrapped lines into their parent bullet, and the
"new entry after a bullet" rule now ignores lines that follow a line ending in a comma
(i.e. mid-sentence wraps). (`structuring.py`)

### 2.7 Hyperlinked contact details invisible to the parser
**Symptom:** Profile B's email/link URLs are rendered as display text ("Email", "LinkedIn",
"GitHub") with the real value only in the PDF link annotation, so email parsed empty.
**Fix:** `backend/app/services/parsers/pdf.py` now extracts link-annotation URIs
(`_extract_link_uris`) into a new `ParsedDocument.links` field;
`structure_text(text, contact_links=…)` folds them into the contact (`mailto:` → email,
otherwise a labelled link). This is SSRF-irrelevant (local PDF annotations only).
(`base.py`, `pdf.py`, `structuring.py`, `resumes.py`)

### 2.8 (Defensive) Unmapped glyphs
Some resume fonts map punctuation to unmapped glyphs. Added a conservative
`_repair_undecodable()` pass that approximates apostrophes/dashes/quotes from context.
(The two test PDFs carry valid Unicode — U+2019/U+2013/U+201C — so this path did not
trigger for them.)

### 2.9 Test-harness defects (not product bugs)
- LaTeX export begins with a comment header, so the E2E signature check was corrected to
  search rather than `startswith`.

### 2.10 Exports printed raw URLs instead of embedded hyperlinks
**Symptom:** the downloaded PDF/DOCX showed the full URL text (`https://…`) inline, which
looked cluttered and was not a clickable link.
**Fix:** PDF now emits real link annotations via reportlab `<a href>` (email as `mailto:`);
DOCX now emits true `w:hyperlink` relationships. Both display a friendly label
(`GitHub`, `LinkedIn`, host name) instead of the raw URL. LaTeX/TXT already labelled links.
Added `backend/app/services/exports/links.py` (`ensure_url`, `link_label`, `mailto`).

### 2.11 Project links captured as display labels ("GitHub") → broken `https://GitHub`
**Symptom:** some resumes render project links as the visible word "GitHub" while the real
repo URL lives only in the PDF link annotation, so `project.link` was the label and the
export fabricated a broken `https://GitHub`.
**Fix:** `ensure_url()` now returns "" for non-URLs (no fabricated links); `_resolve_project_links()`
matches repo annotations (`github.com/<user>/<repo>`) to projects *in order*, and
`_apply_extra_links()` keeps only profile-level links (LinkedIn, GitHub/GitLab profile, one
portfolio) on the contact line so it stays clean.

---

## 3. Parsing results on the two real resumes (after fixes)

`Candidate_Profile_A.pdf` → structure confidence **0.86**
- contact: Professional contact details, LinkedIn + GitHub links
- experience: 1 (`Editorial Head` @ professional student chapter, Aug 2026–Present)
- education: 2 (undergraduate institution and junior college), both with dates + degree
- projects: 3 (AI assistant, healthcare platform, detection system), each with tech list and merged bullets
- skills: 4 groups (Languages, Backend & Databases, Security & Systems, Tools)
- certifications: 2 · achievements: 4 (correctly separated from Experience)
- summary: empty (correct — the resume has no summary section)

`Candidate_Profile_B.pdf` → structure confidence **0.86**
- contact: Professional contact details (email recovered from link annotation), LinkedIn + GitHub links
- experience: 1 (`Research Fellow – Incoming` @ engineering research foundation)
- education: 3 (engineering college, junior college, secondary school), all with dates
- projects: 4, each split correctly with tech and GitHub/Live-demo links
- summary: empty (correct)

---

## 4. End-to-end coverage (both resumes)

`backend/tests/test_e2e_real_resumes.py` drives the full product through the FastAPI app
with the real uploaded PDFs. Each numbered step asserts on the response.

| # | Area | What was exercised | Result |
| --- | --- | --- | --- |
| 1 | Upload & parse | PDF upload, format detection, structure assertions, list/get/versions | pass |
| 2 | Quality analysis | deterministic `POST /resumes/{id}/analyze` (0–10 score, methodology, findings), analyses history | pass |
| 3 | Versioning | duplicate resume, delete copy | pass |
| 4 | Jobs & matching | create JD, parse required skills, `POST /jobs/match`, keyword statuses, breakdown, get/list matches | pass |
| 5 | Discovery | listings, `/recommendations` (≥1 ranked), save + list saved jobs | pass |
| 6 | Career roadmap | create roadmap from JD gaps, milestones present, patch milestone → done, re-read | pass |
| 7 | Projects & assets | create project plan, add evidence, generate README (from evidence) and bio (from resume+job), list, edit asset | pass |
| 8 | Tailoring / recommendation edits | inject weak bullet → suggestions, all `verified`, apply (accept), confirm bullet rewritten, status `accepted` | pass |
| 9 | Portfolio | create, public 404 before publish, publish, public view by slug, list | pass |
| 10 | Applications | create, move to `applied` (timestamp set), list/get, delete | pass |
| 11 | Profile & dashboard | patch profile/onboarding, dashboard aggregates (resume/app/match/roadmap counts) | pass |
| 12 | Company research | SSRF-blocked private URL returns 422 (`no_sources`), list endpoint OK | pass |
| 13 | Exports | PDF/docx/txt/LaTeX downloaded, signatures checked, re-parsed and name verified, bad format → 422 | pass |

### 4.1 Editor + export format-preservation

`test_demo_resume_edit_and_export_roundtrip` (both resumes):
- edits the resume in the editor model: rewrites `summary`, the first experience bullet and
  appends a certification, each carrying a unique marker;
- verifies the **stored** resume reflects the edits;
- creates an explicit new version and confirms version history grows (≥2);
- exports to **PDF, DOCX, TXT, LaTeX**, re-parses each export and asserts:
  - the edited marker survives (format preservation of *edits*), and
  - project structure (a project word) survives (format preservation of *structure*).

Result: **pass for both resumes, all four formats.**

### 4.2 Live server + real AI (Ollama) smoke test

The pytest suites run with `LLM_PROVIDER=none` (deterministic). To exercise the real
provider, a live `uvicorn` server was started with `LLM_PROVIDER=ollama`
(`qwen2.5:1.5b` at `http://localhost:11434`) and driven over HTTP with cookie+CSRF auth,
uploading both real PDFs.

| Step | Resume | Result |
| --- | --- | --- |
| `GET /health`, `/ready`, `/meta/ai-status` | — | ok; AI `available: true`, model `qwen2.5:1.5b` |
| Upload + parse | Profile A | conf 0.86 · 3 projects · 2 education |
| Upload + parse | Profile B | conf 0.86 · 4 projects · 3 education · email recovered |
| `POST /resumes/{id}/analyze` (`use_ai`) | Profile A | `ai_used=true`, score 8.3 (~4.5 s) |
| `POST /resumes/{id}/analyze` (`use_ai`) | Profile B | `ai_used=true`, score 8.1 |
| `POST /tailor/suggestions` (`use_ai`) | Profile A | 11 suggestions, all truth-verified (~12 s) |
| `POST /projects` (`use_ai`) | Profile A | `ai_used=true`, 4 features, 6 milestones (~7 s) |
| `POST /roadmaps` (`use_ai`) | Profile A | model exceeded the 120 s LLM timeout → **graceful fallback** to deterministic (`ai_used=false`, readiness 70, 6 milestones) |
| `POST /tailor/suggestions` (`use_ai`) | Profile B | model timed out → deterministic fallback → 0 suggestions (none of the candidate's bullets start with a weak phrase; the fallback correctly never invents content) |

Takeaways:
- The AI integration works end-to-end against a live local model for fast prompts
  (analysis, tailoring, project planning).
- The heavy prompts (roadmap, and tailoring of the longer resume) exceed the small
  model's speed and hit `llm_timeout_seconds=120`; the app **degrades to deterministic
  output instead of erroring** — the endpoint still returns 2xx.
- 0 tailoring suggestions is correct behavior, not a defect: the deterministic fallback
  only rewrites bullets beginning with weak phrasing (`responsible for`, `worked on`,
  `helped with`, …) and never adds facts (`backend/app/api/v1/tailor.py:_deterministic_rewrites`).

---

## 5. Regression tests added (self-contained, no PDFs required)

Added to `backend/tests/test_parsers.py` using a synthetic resume that mirrors the real
layout (glued dates, company-on-next-line, wrapped bullets, pipe-separated tech,
non-standard "Hackathons & Competitions" heading):
- multiple education entries split with dates and degrees
- company line kept with the role and correct dates
- wrapped bullets merged and `|` tech/link parsed
- achievements heading separated and no summary leakage

---

## 6. Known limitations / notes

- **Per-project link URLs**: repo annotations (`github.com/<user>/<repo>`) are now matched to
  projects in document order; a project whose annotation cannot be matched keeps its visible
  label as plain text (never a fabricated link). Non-repo "live demo" annotations are not
  individually mapped.
- **Wrapped bullets** are merged; extremely long bullets remain separate lines only when
  the continuation begins after sentence-ending punctuation on the previous line.
- **Company research** makes live HTTP requests in production; the test uses a blocked
  private URL, so no external network is required and the suite is deterministic.
- **Frontend browser E2E** (`npm run e2e`): Playwright is listed as a dev dependency but no
  `playwright.config.ts`/specs exist yet, so no browser E2E suite was run. Frontend is
  covered by Vitest component tests + a production build.
- **Local model latency**: with `qwen2.5:1.5b`, long prompts (roadmap, longer-resume
  tailoring) can exceed the 120 s LLM timeout. Results then fall back to deterministic
  logic rather than failing; a larger/faster model (or higher `LLM_TIMEOUT_SECONDS`)
  removes the fallback.
- **Docker** was not run (daemon unavailable); `docker compose config` validates.

---

## 7. How to reproduce

```powershell
# Backend (from backend\)
.\.venv\Scripts\python.exe -m pytest -q

# Frontend (from frontend\)
npm test
npm run build

# Run the whole app locally (from repo root)
.\start.ps1
```

The two demo PDFs must remain at the repository root for the real-resume E2E tests; if
they are removed the tests skip instead of failing.

---

## 8. Seeded demo account & link/UX improvements

### 8.1 Fully-populated demo account

`backend/scripts/seed_demo.py` builds a single, ready-to-show account from
a representative professional resume PDF by driving the **real API** (cookies + CSRF, via FastAPI's `TestClient`)
against the same database the dev server uses. It is idempotent — it resets only the demo
account and rebuilds it.

```
email: demo@resumo.app    password: demo1234
```

Verified populated state after seeding (`GET /dashboard` over a live server):

| Feature | Seeded |
| --- | --- |
| Resume | 1 (parsed PDF, confidence 0.86, timeline headline + summary) |
| Quality analysis | 1 (deterministic score 8.1/10) |
| Job descriptions + matches | 3 (23.1 / 37.5 / 45.8 of 100) |
| Recommended + saved jobs | ranked recommendations, 3 saved |
| Career roadmaps + milestones | 2 roadmaps (6 + 5 milestones; one `done`, one `in_progress`) |
| Project plans + evidence + assets | 2 plans, 2 evidence entries, 7 generated assets |
| Tailoring suggestions | 2 (1 accepted, 1 pending) |
| Portfolio | published at `/p/<slug>` |
| Applications | 5 across `saved → applied → interview → offer → rejected` |
| Profile | fully completed (`onboarding_completed=true`) |
| Company research | 1 (clearly-labelled sample, offline) |

Convenience: `.\start.ps1 -SeedDemo` seeds then launches both services.

### 8.2 Embedded hyperlinks in exports (verified)

Exported the seeded resume over the live API and inspected the files:

- **PDF**: 8 clickable `/URI` link annotations — `mailto:` email, LinkedIn, GitHub profile,
  one portfolio link, and the four project repo URLs. No raw URLs and no broken
  `https://GitHub`.
- **DOCX**: 7 external hyperlink relationships (`github.com/…`, `linkedin.com/…`, …).

### 8.3 UX polish

- Contact links are now editable in the resume editor (`label` + `URL`, with an "open" test
  link) — previously parsed links could not be corrected.
- The live resume preview renders contact links and project links as clickable, labelled
  links (not raw URLs), matching the exports.
- Shared `linkLabel` / `ensureUrl` helpers (`frontend/src/lib/utils.ts`) keep preview, editor
  and exports consistent.
