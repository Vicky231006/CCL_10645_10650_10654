"""Application settings loaded from environment variables.

Values are only ever read from the environment / .env file. No secrets are
hardcoded. Missing optional values degrade gracefully.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # core
    app_env: str = "development"
    debug: bool = True
    app_name: str = "Resumo"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"

    # security
    secret_key: str = "change-me-development-only-secret-key"
    access_token_ttl_minutes: int = 720
    cookie_name: str = "resumo_session"
    csrf_cookie_name: str = "resumo_csrf"
    cookie_secure: bool = False
    cookie_domain: str = ""

    # database
    database_url: str = "sqlite:///./resumo_dev.db"

    # storage
    storage_backend: str = "local"
    local_storage_dir: str = "./storage"
    s3_bucket: str = ""
    s3_region: str = "ap-south-1"

    # ai
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    bedrock_region: str = "ap-south-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    llm_timeout_seconds: int = 120

    # uploads
    max_upload_mb: int = 10
    max_pdf_pages: int = 10

    # jobs
    job_runner: str = "thread"
    sqs_queue_url: str = ""

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def allowed_origins(self) -> list[str]:
        origins = {o.strip() for o in self.frontend_origin.split(",") if o.strip()}
        if self.app_env == "development":
            origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
        return sorted(origins)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def local_storage_path(self) -> Path:
        p = Path(self.local_storage_dir)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        return p


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
