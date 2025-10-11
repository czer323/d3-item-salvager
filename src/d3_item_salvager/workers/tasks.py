"""Background task implementations for the workers module."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from d3_item_salvager.config.settings import AppConfig
    from d3_item_salvager.container import Container
    from d3_item_salvager.services.build_guide_service import (
        BuildGuideService,
        BuildSyncSummary,
    )
    from d3_item_salvager.services.protocols import ServiceLogger


def _ensure_container(container: Container | None) -> Container:
    """Return a container instance, creating a default one when needed."""
    if container is not None:
        return container

    from d3_item_salvager.container import (  # pylint: disable=import-outside-toplevel
        Container as AppContainer,
    )

    return AppContainer()


def _resolve_logger(container: Container) -> ServiceLogger:
    """Resolve the shared service logger from the container."""
    return container.logger()


def _resolve_config(container: Container) -> AppConfig:
    """Resolve the application configuration from the container."""
    return container.config()


def _resolve_build_guide_service(container: Container) -> BuildGuideService:
    """Resolve the build guide service from the container."""
    return container.build_guide_service()


def _log_summary(logger: ServiceLogger, summary: BuildSyncSummary) -> None:
    """Emit a structured log entry summarising a build sync operation."""
    logger.info(
        "Scheduled build guide sync completed.",
        extra={
            "guides_processed": summary.guides_processed,
            "guides_skipped": summary.guides_skipped,
            "builds_created": summary.builds_created,
            "profiles_created": summary.profiles_created,
            "items_created": summary.items_created,
            "usages_created": summary.usages_created,
        },
    )


def scrape_guides_task(
    *, container: Container | None = None, force_refresh: bool = False
) -> None:
    """Synchronise build guides and related profile data.

    Args:
        container: Optional dependency-injector container instance. When omitted a
            new container will be constructed lazily.
        force_refresh: Whether to bypass any cached guide metadata when fetching
            the latest guides from Maxroll.
    """
    app_container = _ensure_container(container)
    logger = _resolve_logger(app_container)
    service = _resolve_build_guide_service(app_container)

    logger.info(
        "Starting scheduled build guide sync.",
        extra={"force_refresh": force_refresh},
    )
    try:
        summary = service.prepare_database(force_refresh=force_refresh)
    except Exception:  # pragma: no cover - defensive logging
        logger.exception(
            "Scheduled build guide sync failed.",
            extra={"force_refresh": force_refresh},
        )
        raise
    _log_summary(logger, summary)


def refresh_cache_task(*, container: Container | None = None) -> None:
    """Refresh the cached guide metadata without persisting to the database."""
    app_container = _ensure_container(container)
    logger = _resolve_logger(app_container)
    service = _resolve_build_guide_service(app_container)

    logger.info("Starting scheduled guide cache refresh.")
    try:
        guides = service.fetch_guides(force_refresh=True)
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("Guide cache refresh failed.")
        raise

    logger.info("Guide cache refresh complete.", extra={"guide_count": len(guides)})


def cleanup_logs_task(*, container: Container | None = None) -> None:
    """Remove log files older than the configured retention age."""
    app_container = _ensure_container(container)
    logger = _resolve_logger(app_container)
    config = _resolve_config(app_container)

    retention_days = max(1, int(config.scheduler.cleanup_logs_max_age_days))
    timezone = ZoneInfo(config.scheduler.timezone)
    cutoff = datetime.now(timezone) - timedelta(days=retention_days)

    log_path = Path(config.logging.log_file)
    log_dir = log_path.parent
    if not log_dir.exists():
        logger.debug("Log directory does not exist; skipping cleanup.")
        return

    removed_files = 0
    for file_path in log_dir.glob("*.log*"):
        if not file_path.is_file():
            continue
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, timezone)
        if mtime < cutoff:
            try:
                file_path.unlink()
                removed_files += 1
            except OSError as exc:  # pragma: no cover - filesystem dependent
                logger.warning(
                    "Failed to remove log file during cleanup.",
                    extra={"path": str(file_path), "error": str(exc)},
                )

    logger.info(
        "Log cleanup completed.",
        extra={"removed_files": removed_files, "retention_days": retention_days},
    )
