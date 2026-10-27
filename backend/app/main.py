"""Resumo FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import applications, auth, career, company, dashboard, discovery, health, jobs, profile, resumes, tailor
from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.services.seed import seed_job_listings

logger = get_logger("resumo.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.debug)
    init_db()
    if not settings.is_sqlite or settings.app_env == "development":
        with SessionLocal() as db:
            created = seed_job_listings(db)
            if created:
                logger.info("seeded sample job listings", extra={"extra_fields": {"count": created}})
    logger.info("resumo started", extra={"extra_fields": {"env": settings.app_env}})
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Resumo API",
        version="1.0.0",
        description=(
            "Resumo — AI resume intelligence, job matching, and career preparation. "
            "Scores are advisory and derived from transparent rules; they are not employer ATS scores."
        ),
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    register_exception_handlers(app)

    prefix = settings.api_v1_prefix
    app.include_router(health.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(profile.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(resumes.router, prefix=prefix)
    app.include_router(jobs.router, prefix=prefix)
    app.include_router(discovery.router, prefix=prefix)
    app.include_router(tailor.router, prefix=prefix)
    app.include_router(career.router, prefix=prefix)
    app.include_router(company.router, prefix=prefix)
    app.include_router(applications.router, prefix=prefix)

    @app.get("/")
    def root() -> dict:
        return {"app": settings.app_name, "docs": "/api/docs", "api": prefix}

    return app


app = create_app()
