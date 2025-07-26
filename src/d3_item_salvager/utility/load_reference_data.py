"""
Script to load reference data into the Diablo 3 Item Salvager database.

- Reads reference data files (e.g., reference/data.json, profile_object_*.json)
- Uses loader functions to insert/validate data
- Only runs when manually executed
"""

from pathlib import Path

from src.d3_item_salvager.data.db import create_db_and_tables, get_session
from src.d3_item_salvager.data.loader import (
    insert_build,
    insert_item_usages_with_validation,
    insert_items_from_dict,
    insert_profiles,
)
from src.d3_item_salvager.maxroll_parser.build_loader import BuildProfileParser
from src.d3_item_salvager.maxroll_parser.data_loader import load_master_data

REFERENCE_DIR = Path.cwd() / "reference"
ITEMS_FILE = REFERENCE_DIR / "data.json"
PROFILE_FILE = REFERENCE_DIR / "profile_object_861723133.json"


def load_items() -> None:
    """Load items from reference/data.json and insert into the database using load_master_data."""
    print(f"Loading items from {ITEMS_FILE}...")
    try:
        item_dict = load_master_data(ITEMS_FILE)
    except Exception as e:
        print(f"Error loading items with parser: {e}")
        return
    with get_session() as session:
        insert_items_from_dict(item_dict, session)
    print("Item loading complete.")


def insert_build_and_profiles(
    json_path: Path, build_id: int, build_title: str | None = None
) -> None:
    """Parse build/profile JSON, insert Build/Profile records, and item usages into the database."""
    print(f"Parsing build/profile from {json_path}...")
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
        print(
            f"Inserted build, {len(profiles)} profiles, and {len(usages)} item usages."
        )
    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
    """Main entry point for loading reference data."""
    create_db_and_tables()  # Ensure tables exist before loading
    # load_items()
    insert_build_and_profiles(
        PROFILE_FILE, build_id=861723133, build_title="Example Build 2"
    )


if __name__ == "__main__":
    main()
