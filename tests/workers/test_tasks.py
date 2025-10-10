"""Unit tests for worker task functions."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

import pytest
from dependency_injector import providers

from d3_item_salvager.config.base import (
    LoggingConfig,
    MaxrollParserConfig,
    SchedulerConfig,
)
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.container import Container
from d3_item_salvager.services.build_guide_service import BuildSyncSummary
from d3_item_salvager.workers import tasks

if TYPE_CHECKING:  # pragma: no cover - typing only
    from pathlib import Path


class FakeLogger:
    """Simple logger capturing emitted log messages for assertions."""

    def __init__(self) -> None:
        self.info_messages: list[tuple[str, dict[str, object] | None]] = []
        self.debug_messages: list[tuple[str, dict[str, object] | None]] = []
        self.warning_messages: list[tuple[str, dict[str, object] | None]] = []
        self.error_messages: list[tuple[str, dict[str, object] | None]] = []
        self.exception_messages: list[tuple[str, dict[str, object] | None]] = []

    @staticmethod
    def _extract_extra(kwargs: dict[str, object]) -> dict[str, object] | None:
        extra = kwargs.get("extra")
        if isinstance(extra, dict):
            normalized = {
                str(key): value
                for key, value in cast("dict[object, object]", extra).items()
            }
            return normalized
        return None

    def debug(self, message: str, *_args: object, **kwargs: object) -> None:
        self.debug_messages.append((message, self._extract_extra(kwargs)))

    def info(self, message: str, *_args: object, **kwargs: object) -> None:
        self.info_messages.append((message, self._extract_extra(kwargs)))

    def warning(self, message: str, *_args: object, **kwargs: object) -> None:
        self.warning_messages.append((message, self._extract_extra(kwargs)))

    def error(self, message: str, *_args: object, **kwargs: object) -> None:
        self.error_messages.append((message, self._extract_extra(kwargs)))

    def exception(self, message: str, *_args: object, **kwargs: object) -> None:
        self.exception_messages.append((message, self._extract_extra(kwargs)))


class FakeBuildGuideService:
    """Fake BuildGuideService implementation for task tests."""

    def __init__(
        self, summary: BuildSyncSummary | None = None, guide_count: int = 0
    ) -> None:
        self.summary = summary or BuildSyncSummary(0, 0, 0, 0, 0, 0)
        self.guide_count = guide_count
        self.prepare_calls: list[bool] = []
        self.fetch_calls: list[bool] = []

    def prepare_database(self, *, force_refresh: bool) -> BuildSyncSummary:
        self.prepare_calls.append(force_refresh)
        return self.summary

    def fetch_guides(self, *, force_refresh: bool) -> list[object]:
        self.fetch_calls.append(force_refresh)
        return [object()] * self.guide_count


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    """Provide a temporary log file for cleanup tests."""
    log_path = tmp_path / "logs" / "app.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("initial", encoding="utf-8")
    return log_path


@pytest.fixture
def app_config(log_file: Path) -> AppConfig:
    """Provide an application config tailored for worker tests."""
    scheduler = SchedulerConfig(job_store_path=log_file.parent / "scheduler.sqlite")
    logging = LoggingConfig(log_file=str(log_file))
    maxroll = MaxrollParserConfig(bearer_token="dummy-token")
    return AppConfig(
        maxroll_parser=maxroll,
        logging=logging,
        scheduler=scheduler,
    )


@pytest.fixture
def container(app_config: AppConfig) -> Container:
    """Create a dependency-injector container for tests."""
    container = Container()
    config_provider = cast("Any", container.config)
    config_provider.override(providers.Object(app_config))
    return container


def _bind_dependencies(
    container: Container,
    *,
    logger: FakeLogger,
    service: FakeBuildGuideService,
) -> None:
    logger_provider = cast("Any", container.logger)
    logger_provider.override(providers.Object(logger))
    service_provider = cast("Any", container.build_guide_service)
    service_provider.override(providers.Object(service))


def test_scrape_guides_task_invokes_prepare_database(
    container: Container,
) -> None:
    """scrape_guides_task should persist build data via BuildGuideService."""
    summary = BuildSyncSummary(1, 0, 1, 2, 3, 4)
    service = FakeBuildGuideService(summary=summary)
    logger = FakeLogger()
    _bind_dependencies(container, logger=logger, service=service)

    tasks.scrape_guides_task(container=container, force_refresh=False)

    assert service.prepare_calls == [False]
    assert any(
        payload
        and payload.get("guides_processed") == 1
        and payload.get("builds_created") == 1
        for _, payload in logger.info_messages
    )


def test_scrape_guides_task_propagates_errors(container: Container) -> None:
    """scrape_guides_task should surface exceptions from the service layer."""

    class RaisingService(FakeBuildGuideService):
        def prepare_database(self, *, force_refresh: bool) -> BuildSyncSummary:
            del force_refresh
            msg = "boom"
            raise RuntimeError(msg)

    service = RaisingService()
    logger = FakeLogger()
    _bind_dependencies(container, logger=logger, service=service)

    with pytest.raises(RuntimeError):
        tasks.scrape_guides_task(container=container)
    assert logger.exception_messages


def test_refresh_cache_task_forces_refresh(container: Container) -> None:
    """refresh_cache_task should fetch guides with force_refresh enabled."""
    service = FakeBuildGuideService(guide_count=3)
    logger = FakeLogger()
    _bind_dependencies(container, logger=logger, service=service)

    tasks.refresh_cache_task(container=container)

    assert service.fetch_calls == [True]
    assert any(
        payload and payload.get("guide_count") == 3
        for _, payload in logger.info_messages
    )


def test_cleanup_logs_task_removes_expired_files(
    container: Container,
    app_config: AppConfig,
    log_file: Path,
) -> None:
    """cleanup_logs_task should remove log files older than retention."""
    retention_days = app_config.scheduler.cleanup_logs_max_age_days
    old_timestamp = (
        datetime.now(tz=UTC) - timedelta(days=retention_days + 1)
    ).timestamp()
    os.utime(log_file, (old_timestamp, old_timestamp))
    service = FakeBuildGuideService()
    logger = FakeLogger()
    _bind_dependencies(container, logger=logger, service=service)

    tasks.cleanup_logs_task(container=container)

    assert not log_file.exists()
    assert any(
        payload and payload.get("removed_files") == 1
        for _, payload in logger.info_messages
    )
