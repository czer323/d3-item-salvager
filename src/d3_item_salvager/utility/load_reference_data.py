"""
Script to load reference data into the Diablo 3 Item Salvager database.

- Reads reference data files (e.g., reference/data.json, profile_object_*.json)
- Uses loader functions to insert/validate data
- Only runs when manually executed
"""

# Standard library

from dataclasses import asdict
from pathlib import Path

# Third-party
from loguru import logger
from sqlmodel import Session, select

# Local/project
from d3_item_salvager.container import Container
from d3_item_salvager.data.db import create_db_and_tables
from d3_item_salvager.data.loader import (
    insert_build,
    insert_item_usages_with_validation,
    insert_items_from_dict,
    insert_profiles,
)
from d3_item_salvager.data.models import ItemUsage, Profile
from d3_item_salvager.logging.setup import setup_logger
from d3_item_salvager.maxroll_parser.build_profile_parser import BuildProfileParser
from d3_item_salvager.maxroll_parser.item_data_parser import DataParser

REFERENCE_DIR = Path.cwd() / "reference"
ITEMS_FILE = REFERENCE_DIR / "data.json"
PROFILE_FILE = REFERENCE_DIR / "profile_object_861723133.json"


def load_items(session: Session) -> None:
    """
    Load items from reference/data.json and insert into the database using DataParser.

    Args:
        session: The database session.

    Returns:
        None

    Raises:
        FileNotFoundError: If the items file is not found.
        ValueError: If item data is invalid.
        RuntimeError: If a runtime error occurs during loading.
    """
    logger.info("Loading items from {}...", ITEMS_FILE)
    try:
        loader = DataParser(ITEMS_FILE)
        item_dict = loader.get_all_items()  # Ensure correct dictionary is passed
    except FileNotFoundError as e:
        logger.error("File not found: {}", e)
        return
    except ValueError as e:
        logger.error("Value error while loading items: {}", e)
        return
    except RuntimeError as e:
        logger.error("Runtime error while loading items: {}", e)
        return
    item_dict_as_dict: dict[str, dict[str, str]] = {}
    for item_id, meta in item_dict.items():
        meta_dict = {
            field: str(value)
            for field, value in asdict(meta).items()
            if value is not None
        }
        item_dict_as_dict[item_id] = meta_dict
    insert_items_from_dict(item_dict_as_dict, session)
    logger.info("Item loading complete.")


def build_item_usages_from_parser(
    parser: "BuildProfileParser", profile_lookup: dict[str, int]
) -> list[ItemUsage]:
    """
    Build a list of ItemUsage objects from parser data and profile lookup.

    Args:
        parser: BuildProfileParser instance to extract usages from.
        profile_lookup: Dictionary mapping profile names to profile IDs.

    Returns:
        list[ItemUsage]: List of valid ItemUsage objects with profile_id set.
    """
    usages: list[ItemUsage] = []
    for u in parser.extract_usages():
        pid = profile_lookup.get(u.profile_name)
        if pid is None:
            logger.error(
                "No profile found for item usage: profile_name={}",
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
    session: Session, json_path: Path, build_id: int, build_title: str | None = None
) -> None:
    """
    Parse build/profile JSON, insert Build/Profile records, and item usages into the database.

    Args:
        session: The database session.
        json_path: Path to the build/profile JSON file.
        build_id: Build ID to use for inserted records.
        build_title: Optional build title.

    Returns:
        None

    Raises:
        FileNotFoundError: If the JSON file is not found.
        ValueError: If data is invalid.
        RuntimeError: If a runtime error occurs during insertion.
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
    """
    Main entry point for loading reference data.

    Returns:
        None
    """
    container = Container()
    app_config = container.config()
    setup_logger(app_config)

    logger.info("Starting reference data loading...")

    engine = container.engine()
    create_db_and_tables(engine)

    with container.session() as session:
        # load_items(session)
        insert_build_and_profiles(
            session, PROFILE_FILE, build_id=861723133, build_title="Example Build 2"
        )


if __name__ == "__main__":
    main()
