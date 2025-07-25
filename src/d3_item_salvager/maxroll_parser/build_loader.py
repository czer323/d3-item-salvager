"""
Loader for Diablo 3 build profile JSON files (e.g., from reference/profile_object_*.json).
Handles quirks and extracts the 'data' key containing build profiles.
"""

import json
from pathlib import Path
from typing import Any


def load_build_profile(file_path: str | Path) -> dict[str, Any]:
    """
    Load and parse a build profile JSON file, returning the 'data' key.
    Args:
        file_path: Path to the build profile JSON file.
    Returns:
        The value of the 'data' key (usually a dict or list of profiles).
    Raises:
        ValueError: If the file is not valid JSON or missing 'data'.
    """
    path = Path(file_path)
    try:
        with path.open(encoding="utf-8") as f:
            content = f.read()
        # Try to parse as JSON
        obj = json.loads(content)
    except Exception as e:
        msg = f"Could not parse build profile JSON: {e}"
        raise ValueError(msg) from e

    if not isinstance(obj, dict) or "data" not in obj:
        msg = "Build profile JSON missing top-level 'data' key."
        raise ValueError(msg)
    data = obj["data"]
    # If data is a string, try to parse it as JSON
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            msg = f"Could not parse 'data' value as JSON: {e}"
            raise ValueError(msg) from e
    return data
