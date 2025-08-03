"""
Utility to extract and pretty-print the 'data' value from a build profile JSON file.
Handles double-encoded JSON and outputs a clean, human-readable format.
"""

import json
import sys
from pathlib import Path
from typing import TypedDict, cast

from loguru import logger


class ProfileDataDict(TypedDict):
    """TypedDict for the expected structure of the 'data' value in a build profile JSON."""

    # Add all expected keys and their types here
    # Example:
    items: dict[str, dict[str, str]]
    profiles: dict[str, dict[str, str]]
    # Add more fields as needed


def extract_data_value(profile_path: str | Path) -> ProfileDataDict:
    """Extracts the 'data' value from a build profile JSON file."""
    path = Path(profile_path)
    with path.open(encoding="utf-8") as f:
        content = f.read()
    obj = json.loads(content)
    # Assume obj is always a dict with a 'data' key containing the expected structure
    data = obj["data"]
    if isinstance(data, str):
        # Handle double-encoded JSON
        data = json.loads(data)
    # Cast to ProfileDataDict for static typing
    return cast("ProfileDataDict", data)


def main() -> None:
    """Main function to run the utility."""
    if len(sys.argv) < 2:
        logger.error("Usage: python export_profile_data.py <profile_json_path>")
        sys.exit(1)
    profile_path = sys.argv[1]
    data = extract_data_value(profile_path)
    logger.info("Extracted profile data:")
    logger.info(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
