"""
Script to extract and print all unique item types from reference/data.json.
"""

from pathlib import Path

from src.d3_item_salvager.maxroll_parser.data_loader import load_master_data

REFERENCE_DIR = Path.cwd() / "reference"
ITEMS_FILE = REFERENCE_DIR / "data.json"


def main() -> None:
    item_dict = load_master_data(ITEMS_FILE)
    types = set()
    for item in item_dict.values():
        item_type = item.get("type", "")
        if item_type:
            types.add(item_type)
    print("Unique item types:")
    for t in sorted(types):
        print(t)


if __name__ == "__main__":
    main()
