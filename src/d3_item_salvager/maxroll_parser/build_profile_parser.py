"""
Loader & parser for Diablo 3 build profile JSON files.

Produces structured BuildProfileData instances plus extracted item usages
(normalised as BuildProfileItems with enumerated slot & usage context).
"""

__all__ = ["BuildProfileData", "BuildProfileParser"]

import json
from pathlib import Path
from typing import Any

from .maxroll_exceptions import BuildProfileError
from .protocols import BuildProfileParserProtocol
from .types import (
    BuildProfileData,
    BuildProfileItems,
    ItemSlot,
    ItemUsageContext,
)


class BuildProfileParser(BuildProfileParserProtocol):
    """
    Parses Diablo 3 build profile JSON files and provides methods
    to extract normalized profiles and item usages.

    Implements BuildProfileParserProtocol for protocol compliance.

    Args:
        file_path: Path to the build profile JSON file.

    Attributes:
        file_path: Path to the build profile JSON file.
        raw_json: Raw loaded JSON data.
        build_data: Parsed build data from the 'data' key.
        profiles: list[BuildProfileData] - List of ProfileData objects extracted from the build.
    """

    def __init__(self, file_path: str | Path) -> None:
        self.file_path: Path = Path(file_path)
        self.raw_json: dict[str, Any] = self._load_json()
        self.build_data: dict[str, Any] = self._extract_data()
        self.profiles: list[BuildProfileData] = self._extract_profiles()

    def parse_profile(self, file_path: str) -> object:
        """
        Parse a build profile from the given file path and return the parsed object.
        Protocol method for BuildProfileParserProtocol.
        """
        parser = BuildProfileParser(file_path)
        return parser

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
        except Exception as e:  # pragma: no cover - unexpected IO/JSON issues
            msg = f"Could not parse build profile JSON: {e}"
            raise BuildProfileError(msg, file_path=str(self.file_path)) from e
        if not isinstance(obj, dict):  # defensive
            msg = "Top level profile JSON must be an object."
            raise BuildProfileError(
                msg,
                file_path=str(self.file_path),
            )
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
        if "data" not in obj:
            msg = "Build profile JSON missing top-level 'data' key."
            raise BuildProfileError(
                msg,
                file_path=str(self.file_path),
            )
        data = obj["data"]
        if isinstance(data, str):  # nested JSON string
            try:
                data = json.loads(data)
            except Exception as e:  # pragma: no cover
                msg = f"Could not parse 'data' value as JSON: {e}"
                raise BuildProfileError(
                    msg,
                    file_path=str(self.file_path),
                ) from e
        if not isinstance(data, dict):
            msg = "Parsed 'data' is not a dict."
            raise BuildProfileError(msg, file_path=str(self.file_path))
        return data

    def _extract_profiles(self) -> list[BuildProfileData]:
        """
        Extract build profiles from the parsed build data.

        Returns:
            list[ProfileData]: List of extracted profiles.
        """
        profiles_raw = self.build_data.get("profiles", [])
        result: list[BuildProfileData] = []
        if not isinstance(profiles_raw, list):  # defensive
            msg = "'profiles' must be a list if present."
            raise BuildProfileError(msg, file_path=str(self.file_path))
        for idx, profile_dict in enumerate(profiles_raw):
            if not isinstance(profile_dict, dict):  # skip invalid entries
                continue
            name = str(profile_dict.get("name", ""))
            class_name = str(profile_dict.get("class", ""))
            seasonal = profile_dict.get("seasonal")
            gender = profile_dict.get("gender")
            paragon = profile_dict.get("paragonLevel")
            try:
                paragon_int = int(paragon) if paragon is not None else None
            except (TypeError, ValueError):
                paragon_int = None
            result.append(
                BuildProfileData(
                    name=name,
                    class_name=class_name,
                    seasonal=bool(seasonal) if seasonal is not None else None,
                    gender=str(gender) if gender is not None else None,
                    paragon_level=paragon_int,
                    raw_profile_index=idx,
                )
            )
        return result

    def extract_usages(self) -> list[BuildProfileItems]:
        """
        Extract item usages from the build profiles.

        Returns:
            list[ItemUsageData]: List of item usages for all profiles.
        """
        profiles_raw = self.build_data.get("profiles", [])
        if not isinstance(profiles_raw, list):
            return []

        def parse_slot(slot: str) -> ItemSlot:
            try:
                return ItemSlot(slot)
            except ValueError:
                return ItemSlot.OTHER

        def extract_main_items(
            profile_dict: dict[str, Any], profile_name: str
        ) -> list[BuildProfileItems]:
            items = profile_dict.get("items", {})
            usages = []
            if isinstance(items, dict):
                for slot, item in items.items():
                    slot_enum = parse_slot(slot)
                    item_id = item.get("id") if isinstance(item, dict) else None
                    if item_id:
                        usages.append(
                            BuildProfileItems(
                                profile_name=profile_name,
                                item_id=str(item_id),
                                slot=slot_enum,
                                usage_context=ItemUsageContext.MAIN,
                            )
                        )
            return usages

        def extract_kanai_items(
            profile_dict: dict[str, Any], profile_name: str
        ) -> list[BuildProfileItems]:
            kanai = profile_dict.get("kanai", {})
            usages = []
            if isinstance(kanai, dict):
                for slot in ("weapon", "armor", "jewelry"):
                    kanai_id = kanai.get(slot)
                    if kanai_id:
                        slot_enum = parse_slot(slot)
                        usages.append(
                            BuildProfileItems(
                                profile_name=profile_name,
                                item_id=str(kanai_id),
                                slot=slot_enum,
                                usage_context=ItemUsageContext.KANAI,
                            )
                        )
            return usages

        def extract_follower_items(
            profile_dict: dict[str, Any], profile_name: str
        ) -> list[BuildProfileItems]:
            follower_items = profile_dict.get("followerItems", {})
            usages = []
            if isinstance(follower_items, dict):
                for slot, raw_item in follower_items.items():
                    slot_enum = parse_slot(slot)
                    item_id = (
                        raw_item.get("id")
                        if isinstance(raw_item, dict)
                        else (raw_item if isinstance(raw_item, str) else None)
                    )
                    if item_id:
                        usages.append(
                            BuildProfileItems(
                                profile_name=profile_name,
                                item_id=str(item_id),
                                slot=slot_enum,
                                usage_context=ItemUsageContext.FOLLOWER,
                            )
                        )
            return usages

        item_usages: list[BuildProfileItems] = []
        for profile_dict in profiles_raw:
            if not isinstance(profile_dict, dict):
                continue
            profile_name = str(profile_dict.get("name", ""))
            item_usages.extend(extract_main_items(profile_dict, profile_name))
            item_usages.extend(extract_kanai_items(profile_dict, profile_name))
            item_usages.extend(extract_follower_items(profile_dict, profile_name))
        return item_usages
