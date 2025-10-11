"""Scheduler helpers for background workers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from d3_item_salvager.logging.adapters import get_loguru_service_logger

from . import tasks

if TYPE_CHECKING:  # pragma: no cover - typing only
    from pathlib import Path

    from d3_item_salvager.config.settings import AppConfig


DEFAULT_SCRAPE_JOB_ID = "scrape_guides"
DEFAULT_REFRESH_JOB_ID = "refresh_guide_cache"
DEFAULT_CLEANUP_JOB_ID = "cleanup_logs"


def build_scheduler(*, config: AppConfig) -> BackgroundScheduler:
    """Create a configured APScheduler instance for the workers module."""
    scheduler_config = config.scheduler
    timezone = ZoneInfo(scheduler_config.timezone)

    job_store_url = _prepare_job_store_url(scheduler_config.job_store_path)
    jobstores = {"default": SQLAlchemyJobStore(url=job_store_url)}
    executors = {"default": ThreadPoolExecutor(scheduler_config.max_workers)}
    job_defaults = {
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": scheduler_config.misfire_grace_seconds,
    }

    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=timezone,
    )
    register_jobs(scheduler=scheduler, config=config)
    return scheduler


def register_jobs(*, scheduler: BackgroundScheduler, config: AppConfig) -> None:
    """Register scheduled jobs according to configuration flags."""
    scheduler_config = config.scheduler
    timezone = ZoneInfo(scheduler_config.timezone)

    if scheduler_config.scrape_guides_enabled:
        scheduler.add_job(
            tasks.scrape_guides_task,
            trigger=_build_interval_trigger(
                minutes=scheduler_config.scrape_guides_interval_minutes,
                timezone=timezone,
            ),
            id=DEFAULT_SCRAPE_JOB_ID,
            replace_existing=True,
            kwargs={"force_refresh": False},
        )

    if scheduler_config.refresh_cache_enabled:
        scheduler.add_job(
            tasks.refresh_cache_task,
            trigger=_build_interval_trigger(
                minutes=scheduler_config.refresh_cache_interval_minutes,
                timezone=timezone,
            ),
            id=DEFAULT_REFRESH_JOB_ID,
            replace_existing=True,
        )

    if scheduler_config.cleanup_logs_enabled:
        scheduler.add_job(
            tasks.cleanup_logs_task,
            trigger=_build_interval_trigger(
                minutes=scheduler_config.cleanup_logs_interval_minutes,
                timezone=timezone,
            ),
            id=DEFAULT_CLEANUP_JOB_ID,
            replace_existing=True,
        )


def start_scheduler(scheduler: BackgroundScheduler) -> None:
    """Start the scheduler if it is not already running."""
    if scheduler.running:
        return

    logger = get_loguru_service_logger()
    logger.info("Starting background scheduler.")
    scheduler.start()


def shutdown_scheduler(
    scheduler: BackgroundScheduler,
    *,
    timeout_seconds: int,
) -> None:
    """Attempt graceful shutdown of the scheduler."""
    if not scheduler.running:
        return

    logger = get_loguru_service_logger()
    logger.info(
        "Shutting down background scheduler.",
        extra={"timeout_seconds": timeout_seconds},
    )
    scheduler.shutdown(wait=True)


def _prepare_job_store_url(job_store_path: Path) -> str:
    """Ensure the scheduler job store path exists and return its URL."""
    job_store_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{job_store_path}"


def _build_interval_trigger(*, minutes: int, timezone: ZoneInfo) -> IntervalTrigger:
    """Create an interval trigger, enforcing a minimum interval of one minute."""
    bounded_minutes = max(1, int(minutes))
    return IntervalTrigger(minutes=bounded_minutes, timezone=timezone)
