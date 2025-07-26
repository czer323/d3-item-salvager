"""
Utility to extract and pretty-print the 'data' value from a build profile JSON file.
Handles double-encoded JSON and outputs a clean, human-readable format.
"""

import json
import sys
from pathlib import Path


def extract_data_value(profile_path: str | Path) -> dict:
    """Extracts the 'data' value from a build profile JSON file."""
    path = Path(profile_path)
    with path.open(encoding="utf-8") as f:
        content = f.read()
    obj = json.loads(content)
    data = obj.get("data")
    if isinstance(data, str):
        # Handle double-encoded JSON
        data = json.loads(data)
    return data


def main() -> None:
    """Main function to run the utility."""
    if len(sys.argv) < 2:
        print("Usage: python export_profile_data.py <profile_json_path>")
        sys.exit(1)
    profile_path = sys.argv[1]
    data = extract_data_value(profile_path)
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
