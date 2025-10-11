"""Unit tests for the scheduler helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from d3_item_salvager.config.base import (
    LoggingConfig,
    MaxrollParserConfig,
    SchedulerConfig,
)
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.workers.scheduler import (
    DEFAULT_CLEANUP_JOB_ID,
    DEFAULT_REFRESH_JOB_ID,
    DEFAULT_SCRAPE_JOB_ID,
    build_scheduler,
    register_jobs,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from pathlib import Path


@pytest.fixture
def app_config(tmp_path: Path) -> AppConfig:
    """Return an AppConfig instance tailored for scheduler tests."""
    scheduler = SchedulerConfig(
        job_store_path=tmp_path / "scheduler.sqlite",
        scrape_guides_interval_minutes=1,
        refresh_cache_interval_minutes=2,
        cleanup_logs_interval_minutes=3,
    )
    logging = LoggingConfig(log_file=str(tmp_path / "logs" / "app.log"))
    return AppConfig(
        maxroll_parser=MaxrollParserConfig(bearer_token="dummy-token"),
        logging=logging,
        scheduler=scheduler,
    )


def test_build_scheduler_registers_default_jobs(app_config: AppConfig) -> None:
    """build_scheduler should register all enabled jobs with expected identifiers."""
    scheduler = build_scheduler(config=app_config)
    job_ids = {job.id for job in scheduler.get_jobs()}
    assert job_ids == {
        DEFAULT_SCRAPE_JOB_ID,
        DEFAULT_REFRESH_JOB_ID,
        DEFAULT_CLEANUP_JOB_ID,
    }


def test_register_jobs_respects_flags(app_config: AppConfig) -> None:
    """register_jobs should skip disabled jobs as dictated by configuration."""
    scheduler = build_scheduler(config=app_config)
    scheduler.remove_job(DEFAULT_REFRESH_JOB_ID)
    app_config.scheduler.refresh_cache_enabled = False

    register_jobs(scheduler=scheduler, config=app_config)

    job_ids = {job.id for job in scheduler.get_jobs()}
    assert DEFAULT_REFRESH_JOB_ID not in job_ids
    assert DEFAULT_SCRAPE_JOB_ID in job_ids
    assert DEFAULT_CLEANUP_JOB_ID in job_ids
