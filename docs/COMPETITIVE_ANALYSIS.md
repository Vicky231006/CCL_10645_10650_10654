# Resumo — Competitive Analysis

> Method: review of publicly documented product capabilities (vendor websites, help centres, independent
> reviews). Vendor marketing claims are marked as such and are not treated as verified. Re-verify before
> citing externally. No competitor source code, UI, or datasets were used.

| Product | Category | Strength (documented) | Limitation / opportunity for Resumo |
|---|---|---|---|
| **Jobscan** | JD matching / ATS | Match rate %, hard/soft skill comparison, keyword list against a pasted JD. | Score is opaque ("match rate" not a real ATS score); weak for students with little experience; little evidence provenance. |
| **Teal** | Tailoring + job tracking | Resume builder, tailoring, job tracker + browser extension, keyword targeting. | Organisational tool first; scoring/feedback light; no source-grounded guidance. |
| **Resume Worded** | Resume feedback | Line-by-line AI feedback and score across categories; LinkedIn review. | Feedback can be generic/repetitive; no roadmap linking gaps → projects → skills. |
| **Rezi** | Resume builder + ATS | ATS-focused builder, bullet-point generator, real-time content scoring. | Template/format centric; not a career-planning tool; limited evidence verification. |
| **Huntr** | Job-search CRM | Tracker, resume/cover-letter storage, Kanban pipeline. | No resume analysis or skill-gap coaching; tracker only. |
| **Simplify** | Autofill + matching | Autofill applications, curated job feed, early-career focus. | Optimised for applying fast; little diagnostic feedback or learning roadmap. |

## Fragmentation map
- **Diagnosis** (quality feedback): Resume Worded, Rezi.
- **JD tailoring**: Jobscan, Teal.
- **Tracking**: Huntr, Teal, Simplify.
- **Learning / gap-closing**: *largely absent* across the category.
- **Source-grounded company research**: *absent*; competitors rely on generic advice.

## Where Resumo differentiates (without unsupported claims)
1. **Evidence provenance everywhere.** Every finding cites the exact resume excerpt or JD requirement
   that caused it. No black-box score.
2. **Student-aware scoring.** Absence of full-time experience is not penalised; projects, coursework,
   internships and research are weighted appropriately.
3. **Gap → project → evidence loop.** Resumo connects a missing requirement to a concrete, achievable
   project brief and the evidence to publish — the step competitors skip.
4. **Truth-preserving AI.** Suggestions are verified against source facts and require approval; Resumo
   will not invent metrics, employers, or credentials.
5. **Open, local-first AI.** Works with a local model (Ollama) and degrades gracefully to deterministic
   analysis — no forced vendor lock-in.

## What Resumo deliberately does NOT do
- No "guaranteed ATS pass", no interview-probability claims, no fabricated jobs or metrics.
- No scraping of restricted profiles; company research is limited to legitimate public sources the user
  supplies or that are openly fetchable, with citations and retrieval dates.
- No pricing/billing features.
