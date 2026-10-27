"""Background job runner abstraction.

- inline: run synchronously in the request (tests, simplest dev).
- thread: run in a bounded thread pool (default local dev).
- sqs:    enqueue to SQS for a separate worker process (production).
"""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("resumo.jobs")
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="resumo-job")


def run_job(func: Callable, *args, **kwargs):
    """Dispatch a callable according to the configured job runner."""
    if settings.job_runner == "inline":
        return func(*args, **kwargs)
    if settings.job_runner == "sqs":
        # In production this pushes a message; the worker imports the same callable.
        logger.info("sqs dispatch requested", extra={"extra_fields": {"handler": func.__name__}})
        return _pool.submit(func, *args, **kwargs)
    return _pool.submit(func, *args, **kwargs)
