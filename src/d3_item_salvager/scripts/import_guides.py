"""Small helper script to import build guides into the database.

Run with:

    python -m d3_item_salvager.scripts.import_guides

This module uses the project's DI container so `.env` is loaded via AppConfig.
"""

from __future__ import annotations

from d3_item_salvager.config.settings import load_runtime_env
from d3_item_salvager.container import Container


def main() -> None:
    load_runtime_env()
    container = Container()
    svc = container.build_guide_service()
    summary = svc.prepare_database(force_refresh=True)
    print("Import summary:", summary)


if __name__ == "__main__":
    main()
