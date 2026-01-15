<!-- D3 Item Salvager Project -->

# D3 Item Salvager

> **Effortless Diablo III item data extraction, analysis, and automation.**

---

## Overview

D3 Item Salvager is a Python-based toolkit for extracting, parsing, and analyzing Diablo III item data from guides, databases, and user profiles. Designed for speed, reliability, and extensibility, it streamlines workflows for players, theorycrafters, and developers.

Project is still in early development, with a focus on building a solid foundation for future features and integrations.

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/czer323/d3-item-salvager/main.svg)](https://results.pre-commit.ci/latest/github/czer323/d3-item-salvager/main)

## Features

- 🔍 **Guide & Profile Parsing:** Extracts build/item data from Maxroll and other sources
- 🗄️ **Database Integration:** SQLite-powered local storage for fast queries
- ⚡ **Automated Workflows:** CLI utilities for batch processing and data export
- 🧩 **Modular Design:** Easily extend with custom parsers, services, and utilities
- 🛡️ **Robust Logging & Error Handling:** Built-in logging and exception management
- 🧪 **Comprehensive Testing:** Unit, integration, and E2E tests included

## Quickstart

```sh
# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Start CLI utility
uv run python -m d3_item_salvager

# Start background workers
uv run python -m d3_item_salvager workers
```

## Project Structure

```text
src/d3_item_salvager/
    config/         # Configuration management
    data/           # Database models, queries, and loaders
    exceptions/     # Custom error types and handlers
    logging/        # Logging setup and middleware
    maxroll_parser/ # Guide and profile parsing logic
    utility/        # Helper scripts and utilities
tests/              # Unit, integration, and E2E tests
docs/               # Implementation plans and documentation
reference/          # Sample data and guides
```

## Usage

### Extract Item Data

```sh
uv run python src/utility/export_profile_data.py --profile <profile_id>
```

### Database Operations

```sh
uv run python src/data/init_db.py
```

**Reset & safety runbook:** For destructive reset and repopulation workflows (backup → drop → migrate/import), see `docs/reset_local_db.md`. This runbook documents safe usage, the `--use-migrations` option, and cautions about running against production databases.


### Custom Parsing

Extend `maxroll_parser/` with your own logic for new guide formats or sources.

### Run Scheduled Jobs

```sh
uv run python -m d3_item_salvager workers
```

The workers process uses APScheduler with a persistent SQLite job store (`cache/scheduler.sqlite` by default). Configure intervals and retention policies through the `SCHEDULER_` environment variables or the `scheduler` section of `AppConfig`.

## Development

> [!TIP]
> Run `uv run pre-commit run --all-files` before every commit to ensure code quality, linting, and tests all pass.

- All configuration uses frozen dataclasses for safety and clarity
- Type annotations and Google-style docstrings required for public APIs
- Pre-commit hooks enforce style, type, and test standards

### Playwright E2E (TypeScript) 🔧

Playwright TypeScript tests live in `frontend/tests/playwright/` and produce an HTML report at `frontend/playwright-report/`.

- Tests use the `test_*.ts` filename pattern (we added this to `playwright.config.ts`).
- Run tests locally with:

```sh
# discover & run tests
npx playwright test --config frontend/tests/playwright/playwright.config.ts

# view the HTML report
npx playwright show-report frontend/playwright-report
```

If you prefer an npm-based workflow, install Playwright with your package manager and add a script, e.g.:

```json
{
  "scripts": {
    "test:e2e": "playwright test --config frontend/tests/playwright/playwright.config.ts"
  },
  "devDependencies": {
    "playwright": "latest"
  }
}
```

Note: Playwright may require a running frontend dev server at `http://127.0.0.1:8001` (the `FRONTEND_BACKEND_URL` task sets this).

## Support & Community

For questions, feature requests, or bug reports, please open a GitHub issue.

---

> [!NOTE]
> This project is not affiliated with Blizzard Entertainment or Maxroll.gg. All trademarks are property of their respective owners.
