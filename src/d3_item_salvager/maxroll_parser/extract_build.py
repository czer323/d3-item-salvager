"""
Loader for Diablo 3 build profile JSON files (e.g., from reference/profile_object_*.json).
Provides robust parsing and extraction of build profiles and item usages for production use.
"""

import json
from pathlib import Path
from typing import Any

from .types import BuildProfileData, BuildProfileItems


class BuildProfileParser:  # pylint: disable=too-few-public-methods
    """
    Parses Diablo 3 build profile JSON files and provides methods
    to extract normalized profiles and item usages.

    Args:
        file_path: Path to the build profile JSON file.

    Attributes:
        file_path: Path to the build profile JSON file.
        raw_json: Raw loaded JSON data.
        build_data: Parsed build data from the 'data' key.
        profiles: List of ProfileData objects extracted from the build.
    """

    def __init__(self, file_path: str | Path) -> None:
        self.file_path: Path = Path(file_path)
        self.raw_json: dict[str, Any] = self._load_json()
        self.build_data: dict[str, Any] = self._extract_data()
        self.profiles: list[BuildProfileData] = self._extract_profiles()

    def _load_json(self) -> dict[str, Any]:
        """
        Load and parse the build profile JSON file.

        Returns:
            dict[str, Any]: Loaded JSON object.

        Raises:
            ValueError: If the file cannot be parsed as JSON.
        """
        try:
            with self.file_path.open(encoding="utf-8") as f:
                content = f.read()
            obj: dict[str, Any] = json.loads(content)
        except Exception as e:
            msg = f"Could not parse build profile JSON: {e}"
            raise ValueError(msg) from e
        return obj

    def _extract_data(self) -> dict[str, Any]:
        """
        Extract and parse the 'data' key from the loaded JSON.

        Returns:
            dict[str, Any]: Parsed build data.

        Raises:
            ValueError: If 'data' key is missing or cannot be parsed.
            TypeError: If parsed 'data' is not a dict.
        """
        obj = self.raw_json
        if not isinstance(obj, dict) or "data" not in obj:
            msg = "Build profile JSON missing top-level 'data' key."
            raise ValueError(msg)
        data = obj["data"]
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception as e:
                msg = f"Could not parse 'data' value as JSON: {e}"
                raise ValueError(msg) from e
        if not isinstance(data, dict):
            msg = "Parsed 'data' is not a dict."
            raise TypeError(msg)
        return data

    def _extract_profiles(self) -> list[BuildProfileData]:
        """
        Extract build profiles from the parsed build data.

        Returns:
            list[ProfileData]: List of extracted profiles.
        """
        profiles_raw = self.build_data.get("profiles", [])
        result: list[BuildProfileData] = []
        for profile_dict in profiles_raw:
            name = profile_dict.get("name", "")
            class_name = profile_dict.get("class", "")
            result.append(BuildProfileData(name=name, class_name=class_name))
        return result

    def extract_usages(self) -> list[BuildProfileItems]:
        """
        Extract item usages from the build profiles.

        Returns:
            list[ItemUsageData]: List of item usages for all profiles.
        """
        profiles_raw = self.build_data.get("profiles", [])
        item_usages: list[BuildProfileItems] = []
        for profile_dict in profiles_raw:
            profile_name = profile_dict.get("name", "")
            # Main items
            items = profile_dict.get("items", {})
            for slot, item in items.items():
                item_id = item.get("id")
                if item_id is not None:
                    item_usages.append(
                        BuildProfileItems(
                            profile_name=profile_name,
                            item_id=item_id,
                            slot=slot,
                            usage_context="main",
                        )
                    )
            # Kanai's Cube items
            kanai = profile_dict.get("kanai", {})
            for slot in ("weapon", "armor", "jewelry"):
                kanai_id = kanai.get(slot)
                if kanai_id is not None:
                    item_usages.append(
                        BuildProfileItems(
                            profile_name=profile_name,
                            item_id=kanai_id,
                            slot=slot,
                            usage_context="kanai",
                        )
                    )
            # Follower items
            follower_items = profile_dict.get("followerItems", {})
            for slot, raw_item in follower_items.items():
                if raw_item:
                    item_id = (
                        raw_item.get("id") if isinstance(raw_item, dict) else raw_item
                    )
                    if item_id is not None:
                        item_usages.append(
                            BuildProfileItems(
                                profile_name=profile_name,
                                item_id=item_id,
                                slot=slot,
                                usage_context="follower",
                            )
                        )
        return item_usages
