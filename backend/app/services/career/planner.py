"""Deterministic project-plan generator (fallback for AI project planning).

Produces an achievable, meaningful project brief that maps to the requested skill/skills.
"""
from __future__ import annotations

TEMPLATES: dict[str, dict] = {
    "backend": {
        "problem": "Demonstrate backend engineering: API design, persistence, testing and deployment.",
        "required_features": [
            "REST API with at least 4 endpoints and input validation",
            "Relational schema with migrations",
            "Authentication or an equivalent access-control mechanism",
            "Automated tests (unit + at least one integration test)",
            "Containerised local run (Dockerfile / docker-compose)",
        ],
        "optional_features": ["Pagination and filtering", "Rate limiting", "Background jobs", "CI pipeline"],
        "stack": ["Python/FastAPI or Node/Express", "PostgreSQL", "Docker", "pytest or Jest"],
        "milestones": [
            "Week 1: data model + migrations, health endpoint",
            "Week 2: core endpoints + validation + tests",
            "Week 3: auth/access control, error handling, docs",
            "Week 4: Docker, CI, README with architecture diagram",
        ],
        "testing": "Unit-test business logic; add one integration test hitting a real (test) database.",
        "demonstrates": ["rest", "sql", "docker", "unit testing"],
        "evidence": ["GitHub repo", "README with architecture diagram", "Screenshots of API docs", "Test run output"],
    },
    "frontend": {
        "problem": "Demonstrate accessible, responsive UI engineering with real state and API integration.",
        "required_features": [
            "Multiple routes with client-side routing",
            "Forms with validation and clear error states",
            "Loading, empty and error states",
            "Responsive layout from 360px upward",
            "Keyboard-accessible components with visible focus",
        ],
        "optional_features": ["Theming", "Internationalisation", "Performance budget/lighthouse audit"],
        "stack": ["React + TypeScript", "Vite", "Tailwind CSS", "Vitest + Testing Library"],
        "milestones": [
            "Week 1: scaffold, routing, design tokens",
            "Week 2: core screens + forms + validation",
            "Week 3: state/data layer, accessibility pass",
            "Week 4: tests, deployment, README",
        ],
        "testing": "Component tests for forms and states; one accessibility check (axe or manual keyboard pass).",
        "demonstrates": ["react", "typescript", "html", "css", "unit testing"],
        "evidence": ["GitHub repo", "Live deployment URL", "Screenshots", "Lighthouse/axe report"],
    },
    "ml": {
        "problem": "Demonstrate honest ML practice: data preparation, evaluation, and reproducibility.",
        "required_features": [
            "Problem framing with a clearly defined target and metric",
            "Reproducible data pipeline (no leakage)",
            "Baseline model plus an improved model",
            "Evaluation with appropriate metrics and an error analysis",
            "Documented limitations and ethical considerations",
        ],
        "optional_features": ["Simple deployment/inference endpoint", "Experiment tracking", "Model card"],
        "stack": ["Python", "scikit-learn or PyTorch", "pandas/NumPy", "Jupyter + tests"],
        "milestones": [
            "Week 1: dataset, EDA, leakage checks",
            "Week 2: baseline + evaluation harness",
            "Week 3: improved model + error analysis",
            "Week 4: write-up, reproducibility script, README",
        ],
        "testing": "Add a test that verifies the metric computation and that the data split is leak-free.",
        "demonstrates": ["python", "machine learning", "numpy", "pandas"],
        "evidence": ["GitHub repo", "Notebook or report", "Reproduce script", "Metric table"],
    },
    "cloud": {
        "problem": "Demonstrate deployable infrastructure and operational thinking.",
        "required_features": [
            "Infrastructure defined as code",
            "Automated CI/CD that deploys to a real environment",
            "Logging and at least one alert/metric",
            "Documented rollback and teardown",
            "Least-privilege IAM",
        ],
        "optional_features": ["Blue/green or canary deploy", "Cost estimate breakdown"],
        "stack": ["Terraform", "AWS (EC2/S3/RDS or lambda)", "GitHub Actions", "Docker"],
        "milestones": [
            "Week 1: minimal Terraform stack + state",
            "Week 2: CI/CD pipeline",
            "Week 3: observability + IAM hardening",
            "Week 4: teardown docs + cost notes + README",
        ],
        "testing": "Terraform validate/plan in CI; a smoke test against the deployed endpoint.",
        "demonstrates": ["aws", "terraform", "ci/cd", "linux", "docker"],
        "evidence": ["GitHub repo", "Architecture diagram", "Cost estimate", "Pipeline run screenshots"],
    },
}


def _pick_template(title: str, skills: list[str]) -> dict:
    text = (title + " " + " ".join(skills)).lower()
    if any(k in text for k in ["ml", "machine learning", "data", "model", "ai", "nlp", "vision"]):
        return TEMPLATES["ml"]
    if any(k in text for k in ["cloud", "devops", "terraform", "kubernetes", "aws", "infra", "pipeline"]):
        return TEMPLATES["cloud"]
    if any(k in text for k in ["frontend", "ui", "react", "web", "css", "design"]):
        return TEMPLATES["frontend"]
    return TEMPLATES["backend"]


def build_project_plan(title: str, skills: list[str], job_requirements: list[str] | None = None) -> dict:
    template = _pick_template(title, skills)
    demonstrates = list(dict.fromkeys(template["demonstrates"] + (job_requirements or [])))
    return {
        "problem": template["problem"],
        "required_features": template["required_features"],
        "optional_features": template["optional_features"],
        "suggested_stack": template["stack"],
        "milestones": template["milestones"],
        "acceptance_criteria": [
            "All required features are present and working end to end.",
            "The project builds and runs from a clean checkout using the README.",
            "Automated tests pass.",
        ],
        "testing": template["testing"],
        "demonstrates": demonstrates[:10],
        "evidence_to_publish": template["evidence"],
        "resume_guidance": (
            "Describe the problem, your specific contribution, the technologies used, and any outcome you can "
            "truthfully state (never invent metrics). Quantify only what you actually measured."
        ),
        "stretch_goals": template["optional_features"],
    }


def default_roadmap_milestones(missing_required: list[str], missing_valuable: list[str]) -> list[dict]:
    milestones: list[dict] = []
    week = 1
    fundamentals = ["data structures", "algorithms", "git", "linux", "sql", "system design"]
    core_fundamentals = [s for s in fundamentals if s in [m.lower() for m in missing_valuable + missing_required]]
    for skill in core_fundamentals[:2]:
        milestones.append({
            "title": f"Strengthen fundamentals: {skill}",
            "kind": "fundamentals", "week": week, "estimated_hours": 12,
            "rationale": f"{skill} is a core requirement referenced by the role.",
            "source_requirement": f"Job lists '{skill}'.",
        })
        week += 1
    for skill in missing_required[:4]:
        milestones.append({
            "title": f"Learn and evidence: {skill}",
            "kind": "skill", "week": week, "estimated_hours": 15,
            "rationale": f"'{skill}' is a required skill you have not yet demonstrated.",
            "source_requirement": f"Job lists '{skill}' as required.",
        })
        week += 1
    for skill in missing_valuable[:3]:
        milestones.append({
            "title": f"Optional boost: {skill}",
            "kind": "skill", "week": week, "estimated_hours": 8,
            "rationale": f"'{skill}' is preferred and would strengthen your match.",
            "source_requirement": f"Job lists '{skill}' as preferred.",
        })
        week += 1
    milestones.append({
        "title": "Build a portfolio project covering the top gaps",
        "kind": "project", "week": week, "estimated_hours": 30,
        "rationale": "Projects turn skills into demonstrable evidence.",
        "source_requirement": "Derived from the job's required stack.",
    })
    return milestones
