"""
Script to load reference data into the Diablo 3 Item Salvager database.

- Reads reference data files (e.g., reference/data.json, profile_object_*.json)
- Uses loader functions to insert/validate data
- Only runs when manually executed
"""

from pathlib import Path

from loguru import logger
from sqlmodel import select

from d3_item_salvager.data.db import create_db_and_tables, get_session
from d3_item_salvager.data.loader import (
    insert_build,
    insert_item_usages_with_validation,
    insert_items_from_dict,
    insert_profiles,
)
from d3_item_salvager.data.models import ItemUsage, Profile
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


def build_item_usages_from_parser(
    parser: "BuildProfileParser", profile_lookup: dict[str, int]
) -> list[ItemUsage]:
    """
    Build a list of ItemUsage objects from parser data and profile lookup.
    For each usage extracted from the parser, attempts to match to a profile
    using (profile_name, class_name).
    Logs an error and skips usages that cannot be matched to a profile.
    Returns only valid ItemUsage objects with a valid integer profile_id.
    """
    usages = []
    for u in parser.extract_usages():
        pid = profile_lookup.get(u.profile_name)
        if pid is None:
            logger.error(
                "No profile found for item usage: profile_name=%s",
                u.profile_name,
            )
            continue
        usages.append(
            ItemUsage(
                profile_id=pid,
                item_id=u.item_id,
                slot=u.slot,
                usage_context=u.usage_context,
            )
        )
    return usages


def insert_build_and_profiles(
    json_path: Path, build_id: int, build_title: str | None = None
) -> None:
    """
    Parse build/profile JSON, insert Build/Profile records, and item usages into the database.
    Steps:
    1. Parse profiles and usages from JSON using BuildProfileParser.
    2. Insert build and profiles into the database.
    3. Query inserted profiles to build a lookup of (name, class_name) -> profile_id.
    4. Use build_item_usages_from_parser to construct ItemUsage objects with valid profile_id.
    5. Insert item usages into the database, logging any unmatched usages.
    """
    logger.info("Parsing build/profile from {}...", json_path)
    try:
        parser = BuildProfileParser(json_path)
        # Convert BuildProfileData to Profile ORM objects
        profiles = [
            Profile(build_id=build_id, name=p.name, class_name=p.class_name)
            for p in parser.profiles
        ]
        if build_title is None:
            build_title = f"Build {build_id}" if build_id else json_path.stem
        with get_session() as session:
            insert_build(build_id, build_title, str(json_path), session)
            insert_profiles(profiles, build_id, session)
            # Query profiles to get their IDs (assuming name/class_name is unique per build)

            db_profiles = list(
                session.exec(select(Profile).where(Profile.build_id == build_id))
            )
            profile_lookup = {p.name: p.id for p in db_profiles if p.id is not None}
            # Build usages with centralized error handling for unmatched profiles
            usages = build_item_usages_from_parser(parser, profile_lookup)
            insert_item_usages_with_validation(usages, session)
        logger.info(
            "Inserted build, %d profiles, and %d item usages.",
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
