"""
Script to extract and print all unique item types from reference/data.json.
"""

from pathlib import Path

from loguru import logger

from d3_item_salvager.maxroll_parser.extract_data import DataParser

REFERENCE_DIR = Path.cwd() / "reference"
ITEMS_FILE = REFERENCE_DIR / "data.json"


def main() -> None:
    """Main function to extract and print unique item types from the data file."""
    loader = DataParser(ITEMS_FILE)
    item_dict = loader.items
    types = set()
    for item in item_dict.values():
        item_type = item.get("type", "")
        if item_type:
            types.add(item_type)
    logger.info("Unique item types:")
    for t in sorted(types):
        logger.info(t)


if __name__ == "__main__":
    main()
