"""
Script to load reference data into the Diablo 3 Item Salvager database.

- Reads reference data files (e.g., reference/data.json, profile_object_*.json)
- Uses loader functions to insert/validate data
- Only runs when manually executed
"""

from pathlib import Path

from loguru import logger

from d3_item_salvager.data.db import create_db_and_tables, get_session
from d3_item_salvager.data.loader import (
    insert_build,
    insert_item_usages_with_validation,
    insert_items_from_dict,
    insert_profiles,
)
from d3_item_salvager.logging.setup import setup_logger
from d3_item_salvager.maxroll_parser.extract_build import BuildProfileParser
from d3_item_salvager.maxroll_parser.extract_data import DataParser

REFERENCE_DIR = Path.cwd() / "reference"
ITEMS_FILE = REFERENCE_DIR / "data.json"
PROFILE_FILE = REFERENCE_DIR / "profile_object_861723133.json"


def load_items() -> None:
    """Load items from reference/data.json and insert into the database using DataParser."""
    logger.info("Loading items from {}...", ITEMS_FILE)
    try:
        loader = DataParser(ITEMS_FILE)
        item_dict = loader.items
    except FileNotFoundError as e:
        logger.error("File not found: {}", e)
        return
    except ValueError as e:
        logger.error("Value error while loading items: {}", e)
        return
    except RuntimeError as e:
        logger.error("Runtime error while loading items: {}", e)
        return
    with get_session() as session:
        insert_items_from_dict(item_dict, session)
    logger.info("Item loading complete.")


def insert_build_and_profiles(
    json_path: Path, build_id: int, build_title: str | None = None
) -> None:
    """Parse build/profile JSON, insert Build/Profile records, and item usages into the database."""
    logger.info("Parsing build/profile from {}...", json_path)
    try:
        parser = BuildProfileParser(json_path)
        profiles = [profile.__dict__ for profile in parser.profiles]
        usages = [usage.__dict__ for usage in parser.extract_usages()]

        if build_title is None:
            build_title = f"Build {build_id}" if build_id else json_path.stem
        with get_session() as session:
            insert_build(build_id, build_title, str(json_path), session)
            insert_profiles(profiles, build_id, session)
            insert_item_usages_with_validation(usages, session)
        logger.info(
            "Inserted build, {} profiles, and {} item usages.",
            len(profiles),
            len(usages),
        )
    except FileNotFoundError as e:
        logger.error("File not found: {}", e)
    except ValueError as e:
        logger.error("Value error: {}", e)
    except RuntimeError as e:
        logger.error("Runtime error: {}", e)


def main() -> None:
    """Main entry point for loading reference data."""
    setup_logger()

    logger.info("Starting reference data loading...")
    create_db_and_tables()  # Ensure tables exist before loading
    # load_items()
    insert_build_and_profiles(
        PROFILE_FILE, build_id=861723133, build_title="Example Build 2"
    )


if __name__ == "__main__":
    main()
