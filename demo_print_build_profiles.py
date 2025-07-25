"""
Demo: Load a build profile JSON and print each profile's name and its item slots/items.
"""

import argparse
from pathlib import Path

from d3_item_salvager.maxroll_parser import build_loader, data_loader

# Path to the reference build profile JSON and master data.json
BUILD_PATH = Path(__file__).parent / "reference" / "profile_object_861723133.json"
DATA_PATH = Path(__file__).parent / "reference" / "data.json"


def print_items(items: dict, item_dict: dict, indent: int = 2) -> None:
    """Prints item slots, item IDs, and item names in a consistent format."""
    pad = " " * indent
    for slot, item in items.items():
        item_id = (
            item.get("id")
            if isinstance(item, dict)
            else item
            if isinstance(item, str)
            else None
        )
        item_name = item_dict.get(item_id, {}).get("name") if item_id else None
        if item_id and item_name:
            print(f"{pad}{slot}: {item_id}  |  {item_name}")
        elif item_id:
            print(f"{pad}{slot}: {item_id}  |  Unknown item name")
        else:
            print(f"{pad}{slot}: (no id)")


def process_build_file(build_path: Path, data_path: Path) -> None:
    """Process a single build file and print all profiles."""
    item_dict, _ = data_loader.load_master_data(data_path)
    data = build_loader.load_build_profile(build_path)
    profiles = data.get("profiles")
    if not profiles:
        print(f"No profiles found in build data: {build_path}")
        return
    print(f"\n=== {build_path.name} ===")
    for idx, profile in enumerate(profiles):
        name = profile.get("name", f"Profile {idx}")
        print(f"\nProfile: {name}")

        # Main character items
        items = profile.get("items") or profile.get("equipped") or {}
        if not items:
            print("  No items found for this profile.")
        else:
            print("  Items:")
            print_items(items, item_dict, indent=4)

        # Follower items (only one follower per profile, or none)
        follower_items = profile.get("followerItems")
        if follower_items and any(
            isinstance(v, dict) and "id" in v for v in follower_items.values()
        ):
            print("  Follower:")
            print_items(follower_items, item_dict, indent=4)

        # Kanai's Cube items (always present)
        kanai = profile.get("kanai")
        if kanai:
            print("  Kanai's Cube:")
            kanai_items = {
                slot: {"id": kanai.get(slot)}
                for slot in ("weapon", "armor", "jewelry")
                if kanai.get(slot)
            }
            print_items(kanai_items, item_dict, indent=4)


def main() -> None:
    """Main function to parse command line arguments and process build files."""
    parser = argparse.ArgumentParser(
        description="Print D3 build profile items from one or more build JSON files."
    )
    parser.add_argument(
        "builds",
        nargs="*",
        help="Path(s) to build profile JSON file(s)",
    )
    parser.add_argument(
        "--data",
        default=str(DATA_PATH),
        help="Path to master data.json (default: reference/data.json)",
    )
    args = parser.parse_args()

    # If no build path is provided, use the default BUILD_PATH
    builds = args.builds if args.builds else [str(BUILD_PATH)]

    data_path = Path(args.data)
    for build_file in builds:
        process_build_file(Path(build_file), data_path)


if __name__ == "__main__":
    main()
