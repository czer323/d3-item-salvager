# Task Scheduling / Background Jobs Module – Implementation Plan (v3)

## Domain & Purpose

Delivers periodic scraping, cache refresh, and maintenance workflows using an in-process scheduler. The module must be observable, resilient to transient failures, fully integrated with existing dependency injection, and runnable both ad-hoc and as a long-lived process without external infrastructure.

## Directory Structure

```directory
src/d3_item_salvager/workers/
    __init__.py
    tasks.py         # Background job definitions (idempotent, container-driven)
    scheduler.py     # Scheduler factory, lifecycle helpers, CLI integration
```

## Tools & Libraries

- `APScheduler`
- Python stdlib
- Existing project dependencies (DI container, logging, services)

## Design Patterns

- Scheduler factory that configures APScheduler using application settings; no module-level singletons to keep tests deterministic.
- Task functions resolve dependencies via the DI container at execution time to avoid stale state.
- Structured logging and retry helpers wrap each task.

## Key Functions & Classes

- `scrape_guides_task()`: Fetches guides, parses build profiles, and synchronizes to the database using `BuildGuideService`.
- `refresh_cache_task()`: Refreshes Maxroll guide cache via `MaxrollGuideFetcher`/cache component (reuse existing services where possible).
- `cleanup_logs_task()`: Performs scheduled housekeeping (e.g., removing stale log files) to keep disk usage bounded.
- `build_scheduler(config: AppConfig, container: Container) -> BackgroundScheduler`: Creates a scheduler configured with job stores, executors, and job defaults sourced from config.
- `start_scheduler(scheduler: BackgroundScheduler)`: Starts the scheduler and registers shutdown hooks.
- Optional CLI command `workers run-scheduler` to invoke the setup/start path.

## Implementation Details

- Job store: `apscheduler.jobstores.sqlalchemy.SQLAlchemyJobStore` backed by SQLite file defined in config (default `cache/scheduler.sqlite`).
- Executors: thread pool executor sized via config (default max 5 workers) to parallelize independent tasks when needed.
- Job defaults: `max_instances=1`, `coalesce=True`, and configurable misfire grace times to guarantee idempotency.
- Scheduler lifecycle: `BackgroundScheduler` owned by CLI/process entry point; start/stop controlled via helper functions and Typer command. On shutdown, ensure `scheduler.shutdown(wait=True)` executes.
- Tasks:
  - Resolve services from the DI container inside the task body to guarantee fresh sessions/config.
  - Wrap work in structured logging and timing metrics using existing logging adapters.
  - Catch domain exceptions, emit warnings, and allow APScheduler retries/backoff to handle transient failures.
- Configuration: Extend `AppConfig` with `scheduler` section containing interval definitions (in minutes), job store path, thread pool size, and enable/disable flags per job.
- Observability: Leverage existing logging setup; consider adding counters in logging metrics module (TODO reference if metrics not yet implemented).

- **Scheduler outline**

    ```python
    def build_scheduler(config: AppConfig, container: Container) -> BackgroundScheduler:
        jobstores = {
            "default": SQLAlchemyJobStore(url=f"sqlite:///{config.scheduler.job_store_path}")
        }
        executors = {
            "default": ThreadPoolExecutor(config.scheduler.max_workers)
        }
        job_defaults = {
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": config.scheduler.misfire_grace_seconds,
        }
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=config.scheduler.timezone,
        )

        register_jobs(scheduler, config, container)
        return scheduler
    ```

- **Tasks outline**

    ```python
    def scrape_guides_task(container: Container) -> None:
        logger = container.logger()
        service = container.build_guide_service()
        logger.info("Starting scheduled build guide sync")
        summary = service.prepare_database(force_refresh=False)
        logger.info(
            "Build guide sync complete",
            extra={
                "guides_processed": summary.guides_processed,
                "builds_created": summary.builds_created,
            },
        )
    ```

    Each task accepts the container (or resolves it via lazy import) to keep functions pure and testable.

## Testing & Extensibility

- Tests must verify:
  - `register_jobs` adds enabled jobs with correct triggers, IDs, and intervals sourced from config.
  - Task functions invoke underlying services and handle exceptions (use fakes and stubbed container providers).
  - Scheduler builder respects disabled jobs and custom settings.
  - CLI command (if added) boots scheduler and handles graceful shutdown.
- To extend:
  - Define task function in `tasks.py` with dependency-resolving logic and docstring documenting behavior/interval.
  - Add config flag + interval.
  - Register job in `scheduler.register_jobs` referencing config flag.
  - Update tests and this document.

## Summary

This implementation plan ensures the workers module:

- Runs on a single process without external brokers while preserving persistence across restarts.
- Leverages existing services and DI container for consistency.
- Supports extensibility through config-driven scheduling and modular tasks.
- Provides tests, logging, and documentation aligned with broader project standards.
