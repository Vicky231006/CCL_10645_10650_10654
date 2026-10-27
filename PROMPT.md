You are my principal product architect, senior full-stack engineer, AI/ML engineer, UX designer, cloud architect, security engineer, QA engineer, and technical project lead.

Your mission is to BUILD RESUMO, a complete, functional, exceptionally polished AI-powered resume intelligence and career preparation platform for engineering students and early-career professionals.

This is an implementation assignment, not a brainstorming exercise. Do not stop at a landing page, static mockup, clickable prototype, or list of recommendations. Inspect the existing repository and environment, make sensible decisions independently, implement the product end to end, run it, test it, fix failures, and document how to deploy it.

Do not ask me to approve every minor decision. Ask questions only when a missing decision genuinely blocks implementation. Never claim that a feature works, a test passed, a service is deployed, or data is verified unless you have evidence.

==================================================
1. PRODUCT VISION
==================================================

Product name: Resumo
Category: AI resume intelligence, job matching, career planning, portfolio generation.
Audience: Engineering students, recent graduates, interns, entry-level applicants, and early-career technical professionals. Optimize for Indian engineering students and international opportunities without assuming all users follow the same hiring conventions.

Core promise:
"Understand where you stand. See what each opportunity requires. Build the evidence to get there."

Resumo must help a user:
1. Upload an existing resume or create one from scratch.
2. Understand its strengths, weaknesses, grammar, completeness, formatting, and ATS readability.
3. Receive transparent resume-quality scores and actionable improvements.
4. Compare their profile against a specific job description.
5. Discover relevant jobs and understand why each is suitable.
6. Identify missing skills, projects, experience, and evidence.
7. Build a personalized roadmap to become a stronger candidate.
8. Find credible learning resources and complete practical projects.
9. Generate job-specific resume versions, portfolio pages, project descriptions, and cover letters.
10. Research target companies using legitimate, publicly available evidence.
11. Manage job applications and track progress in one workspace.
12. Export professional documents and maintain ownership of their career information.

The product should feel like a personal career strategist, not a generic chatbot or a resume-template marketplace.

No pricing page, subscription upsells, checkout, billing system, or fake premium gates. Do not add these.

==================================================
2. FIRST ACTIONS: REPOSITORY INSPECTION AND RESEARCH
==================================================

Before coding:
- Inspect the existing repository, files, package manifests, Git status, available tools, environment variables, and current implementation.
- Preserve working code and user changes. Never overwrite unrelated work.
- Determine the current application entry points, frameworks, routes, and tests.
- Write a concise implementation plan and architecture document.
- Identify any available GitHub, browser, terminal, database, AWS, or deployment integrations and use them where appropriate.
- Do not expose secrets or print environment-variable values.

Research the current resume and career-tech market, including:
- Jobscan: job-description matching and ATS optimization.
- Teal: resume tailoring and job-search organization.
- Resume Worded: resume quality and feedback.
- Rezi, Huntr, Simplify, and relevant student career platforms.
- Current ATS parsing limitations, accessible UI patterns, resume standards, and public job data sources.

Inspect official product documentation and credible independent reviews. Distinguish vendor claims from independently verified findings. Create a concise competitive analysis in docs/COMPETITIVE_ANALYSIS.md.

Identify:
- What competitors do well.
- Which capabilities are fragmented across multiple products.
- Where generic AI writing, opaque scores, repetitive recommendations, inaccessible workflows, poor student guidance, and weak evidence provenance create opportunities.
- What Resumo can differentiate on without making unsupported claims.

Do not copy competitors' proprietary interfaces, source code, datasets, or branding.

Translate findings into concrete product decisions. Research should inform implementation, not delay it indefinitely.

==================================================
3. DESIGN SYSTEM AND VISUAL DIRECTION
==================================================

The UI is a first-class product requirement.

Create an exceptionally clean, premium, understated, old-money-inspired editorial aesthetic. Think refined academic publishing, a high-quality professional journal, and an elegant career advisory firm.

Do NOT use:
- JetBrains Mono or programming-themed typography as the main design language.
- Cringe luxury branding, excessive gold, decorative serif overload, or fake luxury styling.
- Generic purple AI gradients, neon glows, rainbow gradients, or glowing borders.
- Glassmorphism everywhere, excessive blur, floating decorative orbs, or pointless 3D.
- Huge rounded cards around every element.
- Oversized marketing headlines on every dashboard screen.
- Generic SaaS template layouts that look interchangeable with every AI startup.
- Emoji as the primary icon system.
- Fake testimonials, invented customer counts, or fabricated hiring outcomes.

Visual direction:
- Warm ivory, restrained charcoal, muted stone, deep forest or ink accents, and subtle neutral borders.
- A sophisticated, accessible palette with sufficient contrast.
- A refined typography pairing: use a restrained editorial serif such as Source Serif 4 for selected display moments, with a highly legible modern sans-serif such as Inter for navigation, forms, dashboards, and body text.
- Strong typographic hierarchy, deliberate whitespace, precise alignment, quiet dividers, restrained shadows, and excellent document previews.
- Use Lucide icons consistently.
- Motion should be purposeful, subtle, fast, and respectful of reduced-motion preferences.
- Prefer generous whitespace and clear content hierarchy over decorative elements.

Use CSS design tokens for colors, type scales, spacing, radii, shadows, and component states. Build reusable components rather than styling each screen independently.

The product must be excellent at:
- 360px-wide phones and larger mobile screens.
- Tablets, laptops, and desktop displays.
- Keyboard-only use, screen readers, visible focus states, and reduced motion.
- Loading, empty, error, success, retry, and partial-result states.
- Long resumes, long job descriptions, small screens, and slow networks.

Use semantic HTML, accessible forms, meaningful labels, and WCAG 2.2 AA as a target.

The marketing page should be elegant and editorial. The authenticated application should prioritize productivity, clarity, and useful information density.

==================================================
4. TECHNICAL ARCHITECTURE
==================================================

Use this stack unless the existing repository provides a compelling, documented reason to adapt it:

Frontend:
- React with TypeScript.
- Vite.
- Tailwind CSS.
- A well-maintained accessible component foundation such as shadcn/ui, customized to the Resumo design system.
- React Router.
- TanStack Query for server state.
- React Hook Form and Zod for form validation.
- A lightweight state store only when genuinely needed.
- A maintained charting library for simple, accessible score visualizations.
- Vitest and React Testing Library.
- Playwright for end-to-end testing.

Backend:
- Python 3.11 or a compatible stable Python version.
- FastAPI.
- Pydantic v2.
- SQLAlchemy 2.x.
- Alembic migrations.
- PostgreSQL on RDS.
- S3 for private uploaded files and generated artifacts.
- A durable background-job mechanism for expensive document parsing, exports, and AI analysis. Prefer SQS with a worker if infrastructure and credentials are available; provide a functional local development alternative.
- Redis only when justified and configured; do not introduce unnecessary paid infrastructure.

Cloud:
- EC2 for FastAPI and worker deployment.
- S3 for private document storage.
- RDS PostgreSQL for users, profiles, resumes, jobs, analyses, roadmaps, portfolio content, and application history.
- IAM roles with least-privilege permissions.
- Systems Manager Parameter Store or Secrets Manager for secrets.
- CloudWatch for logs, metrics, alarms, and operational visibility.
- HTTPS via a correctly configured domain and TLS termination.
- An architecture that can scale without requiring a full microservices deployment from day one.

Use a modular monolith initially with clearly separated domain modules. Do not introduce multiple independently deployed services merely to make the architecture look sophisticated.

Provide Dockerfiles, docker-compose for local development, health checks, environment templates, migrations, seed data, and deployment documentation.

Do not hardcode credentials, API keys, account IDs, database passwords, or production URLs.

Respect AWS costs. Avoid automatically creating NAT Gateways, always-on load balancers, large EC2 instances, or expensive managed services. Explain cost implications and provide teardown instructions. Never create cloud infrastructure without explicit authorization.

If the AWS environment is unavailable, fully implement and test locally. Do not falsely claim deployment.

==================================================
5. INFORMATION ARCHITECTURE AND ROUTES
==================================================

Create a coherent public website and authenticated workspace.

Public routes:
- /
- /features
- /how-it-works
- /privacy
- /terms
- /login
- /signup

Application routes:
- /app
- /app/onboarding
- /app/profile
- /app/resumes
- /app/resumes/new
- /app/resumes/:id
- /app/resumes/:id/analyze
- /app/jobs
- /app/jobs/:id
- /app/match
- /app/career-roadmap
- /app/projects
- /app/portfolio
- /app/portfolio/:slug
- /app/company-insights
- /app/applications
- /app/settings

Implement actual routing, authorization, data persistence, navigation, and useful empty states. These routes are a starting point, not a reason to create unnecessary pages.

Public landing page:
- Clear positioning and a compelling, restrained hero.
- A real, interactive sample resume-analysis experience using clearly labelled demo data.
- A visual explanation of the workflow.
- Product capabilities presented through realistic interface previews.
- A section showing how students progress from resume gaps to projects and skills.
- Transparent explanation of scoring and AI limitations.
- Clear calls to action.
- No fake social proof, fabricated metrics, or pricing page.

==================================================
6. ONBOARDING AND USER PROFILE
==================================================

Create a fast, accessible onboarding flow that can be skipped or completed progressively.

Capture:
- Current degree, institution, graduation year, and academic information if the user chooses to provide it.
- Target roles and career interests.
- Preferred locations and remote/on-site preferences.
- Technical skills, tools, languages, and relevant coursework.
- Work experience, internships, research, hackathons, and leadership.
- Personal and academic projects.
- GitHub, LinkedIn, portfolio, email, and other professional links.
- Preferred industries and target companies.
- Availability and internship/full-time preferences.

Do not require sensitive information unrelated to the product.

Support incomplete profiles. Let the user add missing information later.

Use this information to personalize job discovery, skill-gap analysis, project suggestions, and career roadmaps.

==================================================
7. UNIVERSAL RESUME UPLOAD AND PARSING
==================================================

Allow users to upload common resume formats:
- PDF, including text-based and scanned PDFs.
- DOCX.
- DOC, with a safe conversion strategy where possible.
- TXT and Markdown.
- RTF.
- ODT.
- LaTeX source files such as TEX.
- HTML.
- Images such as PNG and JPEG when the user has a scanned resume.

Implement an extensible parser registry. Use format-specific parsers and safe conversion tools. Use OCR for scanned documents when configured.

Support multiple files, clear upload progress, file validation, size limits, helpful errors, cancellation where possible, and retry.

Do not promise perfect extraction from every format. Show parsing confidence and allow users to correct extracted content.

Extract a structured resume model:
- Name and professional headline.
- Email, telephone, location, and professional links.
- Summary or objective.
- Education and graduation dates.
- Experience, internships, and responsibilities.
- Projects and project URLs.
- Technical skills and proficiency evidence.
- Certifications.
- Achievements, leadership, research, publications, and extracurriculars.
- Dates, organizations, descriptions, and measurable results where explicitly provided.

Preserve the original upload. Let users compare extracted content with the source document.

Normalize all supported input formats into one editable internal representation.

Implement safe file processing:
- Allowlist extensions and verify actual file signatures.
- Enforce upload size and page limits.
- Generate safe object names.
- Scan uploads for malware when an appropriate scanner is available.
- Never execute uploaded files, LaTeX shell commands, embedded macros, or document scripts.
- Prevent path traversal, decompression bombs, malicious HTML, and parser abuse.
- Store files in private S3 buckets.
- Serve documents through authorization-checked, short-lived signed URLs.
- Keep the original file and derived artifacts separately.
- Never use uploaded documents to train models without explicit, informed consent.

==================================================
8. RESUME QUALITY CHECKER
==================================================

Build a comprehensive resume-quality engine.

Analyze:
- Grammar, spelling, punctuation, and awkward wording.
- Clarity, readability, verbosity, and redundant statements.
- Weak verbs and vague claims.
- Missing or incomplete sections relative to the candidate's career stage.
- Chronology, date consistency, and formatting consistency.
- Contact information and professional-link completeness.
- Project descriptions and broken or malformed URLs.
- Skills unsupported by evidence in the resume.
- Responsibilities that lack explanation of impact.
- Unclear abbreviations and inconsistent terminology.
- ATS parsing risks, such as problematic columns, text boxes, headers, footers, unusual symbols, and image-based content.
- Excessive length, poor information density, and irrelevant content.
- Education and experience ordering.
- Whether the content suits the user's target role and seniority.

Return:
1. Overall quality score out of 10.
2. Category-level scores.
3. Critical issues, important improvements, and optional polish.
4. Exact excerpts that caused each issue.
5. Clear explanations of why each issue matters.
6. Proposed corrections.
7. Accept, edit, reject, and apply-all controls where appropriate.
8. A before-and-after comparison.
9. An improved score after changes, with the methodology disclosed.

Create a transparent scoring rubric. Scores should be derived from deterministic checks wherever possible, with AI-assisted judgments clearly identified. Weight categories explicitly, avoid double-counting issues, and handle missing information fairly.

A student with no work experience must not be penalized as if they were an experienced professional. Evaluate relevant projects, coursework, internships, research, and demonstrable skills instead.

Never guarantee ATS passage or an interview. The score is an advisory assessment, not a hiring probability.

==================================================
9. JOB-SPECIFIC MATCHING AND KEYWORD ANALYSIS
==================================================

Allow users to:
- Paste a job description.
- Supply a job-posting URL where permitted.
- Save a job for future analysis.
- Compare multiple resume versions against the same role.

Parse the description into:
- Required skills.
- Preferred skills.
- Tools, frameworks, and languages.
- Responsibilities.
- Qualifications and education.
- Experience requirements.
- Domain knowledge.
- Certifications.
- Relevant terminology.
- Seniority and location expectations.

Generate a transparent match report containing:
- Overall resume-to-job alignment score.
- Skills explicitly evidenced in the resume.
- Skills mentioned but weakly evidenced.
- Missing or unverified requirements.
- Relevant keywords found and missing.
- Experience and project relevance.
- Education and eligibility considerations.
- Strongest matching resume sections.
- Most important gaps to address.
- Exact recommended edits and their expected relevance.

Create a keyword table with:
Keyword, importance, category, found/missing status, evidence location, and recommended action.

Use semantic similarity as well as exact matching. Normalize equivalent technologies and terminology without treating distinct technologies as interchangeable.

Separate mandatory requirements from preferences. Distinguish an actual missing skill from a missing keyword.

Never insert a keyword simply because it appears in a job description. Do not invent experience, credentials, proficiency, or achievements.

Explain the score's methodology and uncertainty. It is not an employer's actual ATS score.

Support multiple versions of the resume, with a history of job-specific tailoring and clear version labels.

==================================================
10. RELEVANT JOB DISCOVERY
==================================================

Build a useful job discovery and recommendation system.

Prioritize legitimate sources with authorized APIs, feeds, or explicit permission. Evaluate official employer career pages, public job feeds, and supported job-provider integrations. Check current terms, rate limits, attribution rules, and availability.

Do not bypass logins, CAPTCHAs, paywalls, or anti-bot protections. Do not scrape sites in violation of their terms.

Normalize listings into a common schema:
- Title and company.
- Job description.
- Skills and qualifications.
- Location and work arrangement.
- Internship/full-time status.
- Experience level.
- Posting date when known.
- Closing date when known.
- Source and canonical application URL.
- Last verified timestamp.
- Expired or unverified status.

Rank roles by:
- Evidence-based skill alignment.
- Relevant project and experience evidence.
- Education and eligibility fit.
- Career interests.
- Location and work preferences.
- Seniority fit.
- Posting freshness where verified.

Explain why each job is recommended and what could improve the match.

Provide filters, search, sorting, save/skip actions, and job detail views.

Avoid fabricated jobs, invented deadlines, fake salary ranges, and misleading freshness labels.

If live integrations are unavailable, build the complete job module using clearly labelled seed data and an adapter architecture. Never present demo listings as live vacancies.

==================================================
11. "WHAT DO I NEED TO GET THIS JOB?" CAREER GAP COACH
==================================================

This is one of Resumo's flagship features.

A user should be able to say:
"I want to get a software engineering internship at Company X. Here is my current resume and the role I want."

Produce a personalized career gap report:
- Skills already demonstrated.
- Skills required but not demonstrated.
- Skills that would be valuable but are not mandatory.
- Project evidence the candidate should develop.
- Relevant coursework and fundamentals.
- Internship, research, open-source, or teamwork experience that could strengthen the profile.
- Missing evidence of impact, ownership, or technical depth.
- Recommended order of preparation.
- An actionable weekly roadmap with milestones and estimated effort.
- Readiness checkpoints and portfolio deliverables.

Every recommendation must explain its rationale and identify the job-description requirement or verified source that supports it.

Do not tell a student to learn every technology in a job description. Prioritize the highest-impact, achievable gaps.

For every recommended skill:
- Explain what it is and why it matters.
- Specify prerequisite concepts.
- Recommend a learning sequence.
- Find suitable resources with valid links.
- Prefer official documentation, reputable free courses, university materials, and practical tutorials.
- Identify exercises or assessment tasks that demonstrate understanding.

For every recommended project:
- Provide a meaningful project brief.
- State the problem being solved.
- Define required features and optional extensions.
- Suggest an appropriate stack and architecture.
- Define milestones, acceptance criteria, and testing requirements.
- Explain which job requirements the project demonstrates.
- Suggest what evidence to publish: GitHub repository, README, screenshots, architecture diagram, tests, demo, or deployment.
- Explain how to document the project honestly on a resume.
- Include stretch goals only when useful.

Projects must be achievable by the candidate's likely experience level. Avoid recommending generic clones without a meaningful technical objective.

Build a roadmap that updates as the user completes milestones. Allow manual completion, evidence links, notes, and revised recommendations.

Never imply that completing a suggested project guarantees selection.

==================================================
12. EXPERIENCE AND PROJECT EVIDENCE
==================================================

Evaluate domain-relevant evidence fairly.

For an entry-level software engineering role, consider relevant programming projects, data structures, testing, Git, APIs, databases, teamwork, and internship experience when supported by the role.

For ML roles, consider datasets, evaluation methodology, reproducibility, leakage prevention, model performance, deployment, and documentation.

For cloud or DevOps roles, consider deployment architecture, infrastructure as code, CI/CD, monitoring, reliability, security, and operational evidence.

Adapt the criteria to the actual job description rather than enforcing a universal checklist.

Create a project evidence profile with:
- Project title and description.
- Problem and intended users.
- Candidate's actual contribution.
- Technologies used.
- Architecture and engineering decisions.
- Tests and validation.
- Measured outcomes only when supported.
- GitHub, live demo, and documentation links.
- Areas the candidate can confidently explain in an interview.

Ask focused questions when evidence is missing. Turn the candidate's real answers into clearer professional writing without changing the facts.

Never fabricate projects, work history, GitHub activity, impact metrics, user counts, or technical accomplishments.

==================================================
13. RESUME BUILDER: JAKE'S RESUME TEMPLATE
==================================================

Provide a fully functional resume editor with a professional live preview.

Use Jake's Resume LaTeX template as a primary starting template:
https://www.overleaf.com/latex/templates/jakes-resume/syzfjbzwjncs
Reference source:
https://github.com/jakegut/resume

Verify the template's license and attribution requirements before adapting it. Preserve applicable copyright and license notices. Do not claim ownership of third-party templates.

Build a faithful, clean, single-column, ATS-conscious rendition of the template as the default resume layout, preserving its practical strengths and recognizable structure.

The experience must NOT require users to know LaTeX.

Implement:
- Guided forms for every resume section.
- Inline editing and section reordering.
- Add, remove, hide, and restore sections.
- Editable bullet points.
- Live A4 and US Letter previews.
- Page-break and overflow warnings.
- Consistent typography, spacing, margins, and dates.
- One-page and multi-page layouts where appropriate.
- Undo/redo where feasible.
- Autosave with visible save status.
- Version history and duplication.
- A job-specific tailoring mode.
- Section completeness checks.
- A printable version.
- PDF export.
- DOCX export.
- Editable LaTeX source export.
- Plain-text export.
- Import from an existing structured resume.

Support A4 as a natural default for Indian users and provide US Letter as an option.

Use a reliable export pipeline. If PDF or DOCX generation depends on a missing binary or external service, report it clearly and implement an appropriate alternative.

Validate that generated documents preserve selectable text, hyperlinks, correct dates, and reasonable ATS parsing.

The builder must work without an AI provider configured. Manual editing, saving, previewing, and exporting are core functionality.

==================================================
14. AI RESUME TAILORING AND BULLET REWRITING
==================================================

Given a resume and a job description:
- Identify the most relevant existing experiences and projects.
- Recommend section ordering.
- Rephrase real achievements for clarity and relevance.
- Suggest stronger action verbs.
- Improve the expression of technical decisions and outcomes.
- Surface legitimate evidence that is currently buried.
- Propose concise, role-specific summaries when appropriate.
- Recommend the most relevant skills from the candidate's existing profile.
- Generate multiple alternative bullet formulations when useful.

Use a truth-preserving generation pipeline:
1. Extract facts and provenance from the original resume.
2. Generate suggestions tied to those facts.
3. Check suggestions against the source facts.
4. Flag unsupported claims, invented metrics, or changed dates.
5. Present changes as reviewable suggestions.
6. Require the user to approve changes before applying them.

If a stronger metric could improve a bullet, ask the candidate for the real metric instead of inventing one.

Maintain an audit trail of accepted edits and their source.

==================================================
15. COMPANY INTELLIGENCE AND CREDIBLE EXAMPLES
==================================================

Build a company research workspace for candidates applying to specific organizations.

For each target company, gather information from legitimate public sources:
- Official careers pages.
- Official engineering blogs and technical publications.
- Publicly accessible employee profiles.
- Public GitHub repositories and open-source contributions.
- Public conference talks, technical presentations, and interviews.
- Publicly shared resumes or portfolios when their publication and reuse are appropriate.
- Public job descriptions and hiring guidance.

Allow the user to inspect sources and dates.

A candidate may ask:
"How do engineers at this company present their skills and projects?"

Show legitimate examples where available, including:
- Publicly shared professional profiles.
- Voluntarily published resumes and portfolios.
- Publicly available technical projects.
- Recurring themes across multiple credible examples.
- The actual job requirements that connect those themes to the target role.

Do not scrape private or restricted profiles. Do not expose personal email addresses or phone numbers discovered through research. Do not reproduce someone's full resume without permission.

Do not claim a person currently works at a company unless a credible, current public source supports that claim. Label outdated evidence appropriately.

Never invent employee resumes, qualifications, hiring preferences, interview outcomes, or insider information.

When individual examples are unavailable, show aggregated patterns from public job descriptions and official engineering resources instead.

Provide source links, retrieval dates, and confidence indicators. Distinguish verified facts from reasonable inferences.

The objective is to learn from credible public evidence, not copy another candidate's identity or work.

==================================================
16. PORTFOLIO AND PROJECT ASSET GENERATOR
==================================================

Generate editable portfolio assets from verified project information.

Support:
- Professional portfolio website content.
- Project case studies.
- GitHub README drafts.
- Project summaries and technical highlights.
- Architecture descriptions.
- Feature lists and setup instructions.
- Technical documentation outlines.
- Demo-page content.
- LinkedIn headline and About-section drafts.
- Professional biography.
- Cover letters.
- Recruiter outreach drafts.
- Internship application emails.
- Project presentation outlines.

Each project case study should support:
- Problem statement.
- Context and constraints.
- Candidate's individual contribution.
- Architecture and technology choices.
- Implementation decisions.
- Testing and validation.
- Challenges and trade-offs.
- Results and limitations.
- Screenshots, repository, demo, and documentation links.
- Future improvements.

Allow editing before publishing or exporting.

Do not invent project screenshots, deployments, test results, customers, metrics, collaborators, or accomplishments.

Portfolio publishing should be opt-in. Provide a clean public portfolio template, preview, unpublish controls, and explicit visibility settings.

==================================================
17. CONTACTS, LINKS, AND PROFESSIONAL PRESENCE
==================================================

Parse and validate:
- Email.
- Telephone number.
- LinkedIn URL.
- GitHub URL.
- Personal portfolio.
- Project repository URLs.
- Live demos.
- Publications and certifications where applicable.
- Other professional social links explicitly supplied by the user.

Show broken-link warnings when checks can be performed safely. Do not claim that a URL is valid merely because it matches a pattern.

Let users choose which links appear on their resume and portfolio.

Use appropriate link labels and clickable hyperlinks in exported documents. Avoid displaying long raw URLs when a clean link label works.

Do not expose contact details on a public portfolio without explicit consent.

==================================================
18. APPLICATION TRACKER
==================================================

Provide a useful job application workspace with:
- Saved jobs.
- Application status.
- Company and role.
- Job URL and source.
- Date saved and application date.
- Resume version used.
- Cover letter version.
- Contact and follow-up notes.
- Interview dates and preparation notes.
- Deadlines only when verified.
- Rejection, interview, offer, and withdrawal statuses.
- Search, filters, sorting, and timeline views.

Allow a user to connect an application to its job match report, tailored resume, company research, and career roadmap.

Make the experience quick to use on mobile.

Do not submit job applications automatically or send messages to employers without explicit user action.

==================================================
19. AI PROVIDER AND INTELLIGENCE LAYER
==================================================

Create a provider-agnostic AI abstraction.

Support configuration of an appropriate hosted LLM through environment variables, with optional local or alternative providers where practical.

Do not bind the entire product to a single model vendor.

Separate:
- Deterministic parsing and validation.
- Keyword and rule-based analysis.
- Semantic retrieval and similarity.
- AI-assisted reasoning and writing.
- Source retrieval.
- Scoring and calibration.
- Output validation.

Use typed Pydantic schemas for structured model output. Validate all generated content before storing or displaying it.

Build prompt templates for:
- Resume quality review.
- Job-description extraction.
- Resume-job comparison.
- Skill gap analysis.
- Project planning.
- Resume bullet rewriting.
- Portfolio asset generation.
- Company research synthesis.

Treat uploaded documents, job descriptions, websites, and retrieved content as untrusted input. They may contain prompt injection attempts. Never allow document text to override system instructions, invoke tools arbitrarily, access secrets, or change authorization rules.

Use bounded input sizes, sensible timeouts, retries, rate limits, structured errors, and graceful fallbacks.

Track provider errors and token usage where supported, without logging sensitive resume contents.

Cache only when appropriate, isolate user data, and avoid sending documents to external AI providers without clear disclosure and a valid configuration.

If no AI provider is configured, the product must still provide deterministic resume parsing, keyword comparison, profile management, editing, and export. AI-specific actions should show a clear configuration message rather than pretending to generate real results.

==================================================
20. DATA MODEL AND PERSISTENCE
==================================================

Design normalized PostgreSQL models and migrations for:
- Users and authentication identities.
- User profiles and preferences.
- Resume documents and versions.
- Parsed resume sections and evidence.
- Analysis runs and score breakdowns.
- Job listings and sources.
- Job matches and keyword evidence.
- Skill profiles.
- Career roadmaps and milestones.
- Learning resources.
- Project plans and project evidence.
- Portfolio pages and publication settings.
- Generated assets.
- Saved jobs and applications.
- Company research and citations.
- Background jobs and job status.
- Audit events and consent records.

Use UUIDs or another consistent non-guessable identifier strategy.

Include ownership and authorization checks for every user-specific record.

Use transactions for related changes. Add indexes for real query patterns. Use pagination and filtering on list endpoints.

Store uploaded binaries in S3, not PostgreSQL. Store object keys and metadata in the database.

Implement deletion workflows that cover related records, files, derived artifacts, and appropriate retention policies.

Create reproducible migrations and realistic development seed data that is clearly identified as sample data.

==================================================
21. API DESIGN
==================================================

Implement versioned REST APIs under /api/v1.

Create documented endpoints for:
- Authentication and current user.
- Profile management.
- Resume upload, parse, retrieve, edit, duplicate, and delete.
- Resume quality analysis.
- Job description submission and parsing.
- Job matching and keyword reports.
- Job discovery and saved jobs.
- Skill gap reports and roadmaps.
- Project recommendations and milestones.
- Resume generation, versions, and exports.
- Portfolio assets and publishing.
- Company research.
- Application tracking.
- Background job status.
- Health and readiness checks.

Use consistent HTTP status codes, typed request and response schemas, pagination, and a predictable error format.

Generate OpenAPI documentation from FastAPI.

Use secure upload initiation or server-side upload validation, depending on the selected upload design. Never trust client-supplied object keys.

Prevent insecure direct object references by enforcing authorization on every resource lookup.

Avoid exposing internal stack traces or provider secrets in API errors.

==================================================
22. AUTHENTICATION, SECURITY, AND PRIVACY
==================================================

Implement production-minded authentication with secure session handling or a well-supported identity provider.

For cookie-based sessions, use Secure, HttpOnly, and appropriate SameSite settings, plus CSRF protections where needed. If bearer tokens are used, avoid storing sensitive long-lived tokens in localStorage.

Implement:
- Password hashing with a modern password-hashing algorithm if passwords are managed locally.
- Email verification and password reset flows where supported.
- Login throttling and rate limiting.
- Session revocation.
- Ownership checks.
- Input validation.
- Output encoding.
- SQL injection protection through parameterized database operations.
- CORS restricted to configured origins.
- SSRF protection for user-supplied URLs and link previews.
- File upload security.
- Secure HTTP headers.
- Audit logging for security-relevant actions.
- Secrets management.
- Dependency and vulnerability checks.
- Explicit data-retention and deletion behavior.

Never commit .env files or secrets. Provide .env.example containing placeholders only.

Make privacy understandable. Explain when data is sent to AI providers, what is stored, and how to delete an account and its data.

Do not collect sensitive personal data unnecessarily. Do not use resume information for hidden profiling or unrelated purposes.

==================================================
23. DASHBOARD AND PROGRESS EXPERIENCE
==================================================

Create a personalized dashboard that immediately answers:
- What should I work on next?
- Which roles are currently relevant?
- What are my strongest demonstrated skills?
- What gaps matter most for my target role?
- What tasks or project milestones are unfinished?
- Which resumes and applications require attention?

Possible modules:
- Current target role.
- Resume quality summary.
- Recent job-match reports.
- Recommended next actions.
- Skill development progress.
- Active projects.
- Saved jobs and applications.
- Recent resume versions.

Do not reduce career readiness to a single misleading number. Use meaningful progress indicators with transparent definitions.

Show useful empty states and contextual calls to action for new users.

Never make up activity or progress to make the dashboard appear populated.

==================================================
24. TESTING AND QUALITY GATES
==================================================

Testing is mandatory, not optional.

Backend:
- Unit tests for parsers, scoring rules, keyword extraction, authorization, and schemas.
- Integration tests for PostgreSQL, S3 adapters, and API routes.
- Authentication and access-control tests.
- Malformed document and upload security tests.
- AI provider failure and invalid-output tests.
- Migration tests.
- Export validation tests.

Frontend:
- Component tests.
- Form validation tests.
- Responsive layout checks.
- Keyboard navigation and accessibility checks.
- Loading, error, retry, and empty-state tests.
- API integration tests.
- Editor autosave and versioning tests.

End-to-end:
1. Register or sign in.
2. Complete onboarding.
3. Upload a sample resume.
4. Parse and correct extracted information.
5. Run a quality analysis.
6. Submit a sample job description.
7. Review matching keywords and gaps.
8. Generate and approve a truthful resume edit.
9. Create a project roadmap.
10. Save an application.
11. Edit a resume.
12. Export a PDF and DOCX.
13. Verify the exported files.
14. Confirm user A cannot access user B's data.
15. Delete a resume and verify the deletion behavior.

Test representative DOCX, PDF, scanned PDF, TXT, RTF, and LaTeX inputs. Include malformed and oversized uploads.

Run linting, formatting checks, type checking, migrations, unit tests, integration tests, and end-to-end tests where the environment supports them.

Never report tests as passed if they were not run. Clearly document blocked tests and the reason.

==================================================
25. IMPLEMENTATION ORDER
==================================================

Build in complete, testable vertical slices.

Phase 1 — Foundation:
- Inspect repository.
- Establish design tokens and layout.
- Set up frontend, backend, Docker, database, migrations, and health checks.
- Create authentication and protected routes.
- Establish error handling and logging.

Phase 2 — Resume workflow:
- Multi-format upload.
- Parsing and structured resume model.
- Editable resume profile.
- Quality scoring and actionable feedback.
- Resume persistence and history.

Phase 3 — Job matching:
- Job-description parsing.
- Keyword analysis.
- Transparent match scoring.
- Evidence-based recommendations.
- Saved job descriptions and match history.

Phase 4 — Resume builder:
- Jake's Resume-inspired template.
- Live preview.
- Editing and section ordering.
- Tailoring with user approval.
- PDF, DOCX, LaTeX, and plain-text exports.

Phase 5 — Career development:
- Skill-gap reports.
- Learning-resource recommendations.
- Personalized project plans.
- Milestones and evidence tracking.
- Portfolio asset generation.

Phase 6 — Discovery and company intelligence:
- Job-provider adapters.
- Search and ranking.
- Source-grounded company research.
- Application tracking.

Phase 7 — Production hardening:
- Accessibility.
- Security review.
- Performance optimization.
- Test coverage.
- AWS deployment configuration.
- Documentation and operational readiness.

At the end of every phase:
- Run the relevant tests.
- Fix regressions.
- Verify the actual user workflow.
- Update the implementation checklist.

You may reorganize these phases when repository constraints require it, but do not silently skip core requirements.

==================================================
26. DEFINITION OF DONE
==================================================

The product is not complete merely because the homepage looks good.

A feature is done when:
- Its frontend exists and is usable.
- Its backend behavior is implemented where required.
- Data persists correctly.
- Loading, empty, success, and failure states work.
- Authorization and validation are enforced.
- It has appropriate tests.
- It is accessible and responsive.
- It is documented.
- It has been tested against the actual implementation.

Core acceptance criteria:
- A user can upload a supported resume, correct the parsed information, analyze it, and save the results.
- Resume quality scores have explainable criteria and actionable findings.
- A job description produces evidence-backed match and keyword reports.
- The user can edit a resume and export usable documents.
- The AI does not silently invent candidate achievements.
- Skill gaps produce practical, source-supported development plans.
- Projects and portfolio assets remain editable and truth-preserving.
- Saved jobs, roadmaps, resume versions, and applications persist.
- User data is protected across accounts.
- Unsupported integrations fail honestly and gracefully.
- The UI is polished, responsive, and consistent.
- A developer can reproduce the application locally from the documentation.

==================================================
27. FINAL WORKING RULES
==================================================

- Build the real system, not just mockups.
- Use sensible defaults and make progress autonomously.
- Do not replace existing working functionality without reason.
- Do not generate massive, unmaintainable files when modular code is appropriate.
- Do not use fake data to conceal missing functionality.
- Demo data is permitted only when explicitly labelled.
- Do not invent credentials, employee profiles, jobs, or external evidence.
- Do not hardcode secrets.
- Do not deploy, incur cloud charges, or make public releases without authorization.
- Do not add pricing or billing features.
- Do not sacrifice usability for unnecessary complexity.
- Do not claim production readiness without evidence.
- Record important architectural decisions.
- Keep a concise task checklist and update it as work progresses.
- If a tool, credential, or service is unavailable, implement the rest and document the precise blocker.
- If the repository has an established working stack, adapt thoughtfully instead of destroying it to match a preferred stack.
- If time or execution limits intervene, prioritize a working, tested end-to-end core over a huge number of empty screens.

==================================================
28. START NOW
==================================================

First inspect the current repository and available execution environment.

Then:
1. Summarize the existing state and identify constraints.
2. Write the implementation plan and technical architecture.
3. Research competitors and document actionable gaps.
4. Establish the design system and application shell.
5. Implement the first complete vertical slice.
6. Run tests and fix failures.
7. Continue through the roadmap without waiting for approval at every stage.
8. Keep documentation, task status, and environment setup instructions current.

When finished, report:
- What is genuinely implemented.
- The exact routes and workflows verified.
- Tests actually run and their results.
- Features still incomplete.
- External API keys or credentials required.
- How to run the application locally.
- How to deploy to AWS.
- Estimated infrastructure costs and cost controls.
- Security limitations and operational risks.
- The next highest-priority improvements.

Build Resumo as a cohesive, trustworthy, beautiful career platform that students can genuinely use—not an AI-themed mockup.


u also shud be able to exprot a new pdf after ai tells u to make xyz changes in it like if say ai says use this JD instead of this u shud be directly able to export in ur format like directly the pdf

also give an pdf editor interface as well where in u can direcly just edit the pdf s of the resume of the client like he can do it in browser and shit shhud get exported proprely devise a proper strategy for it as well

for ai llm intergration i have a local qwen model installed ppull via ollama im using that for testing currenly now u can go ahead 

