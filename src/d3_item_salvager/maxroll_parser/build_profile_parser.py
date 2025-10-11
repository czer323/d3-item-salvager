"""
Loader & parser for Diablo 3 build profile JSON files.

Produces structured BuildProfileData instances plus extracted item usages
(normalised as BuildProfileItems with enumerated slot & usage context).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import requests

from .guide_profile_resolver import GuideProfileResolver
from .maxroll_exceptions import BuildProfileError
from .protocols import BuildProfileParserProtocol
from .types import (
    BuildProfileData,
    BuildProfileItems,
    ItemSlot,
    ItemUsageContext,
)

__all__ = ["BuildProfileData", "BuildProfileParser"]


if TYPE_CHECKING:  # pragma: no cover - typing only
    from d3_item_salvager.config.settings import AppConfig


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

    def __init__(
        self,
        file_path: str | Path,
        *,
        resolver: GuideProfileResolver | None = None,
        config: AppConfig | None = None,
    ) -> None:
        # keep original input string because Path(file_path) will normalize
        # URL strings (e.g. 'https://...') into OS paths which removes the
        # '//' part on Windows. Use `_input` to detect http(s) URLs.
        self._input: str = str(file_path)
        self.file_path: Path = Path(file_path)
        self._config = config
        self._resolver = resolver or (GuideProfileResolver(config) if config else None)
        self.raw_json: dict[str, Any] = self._load_json()
        self.build_data: dict[str, Any] = self._extract_data()
        self.profiles: list[BuildProfileData] = self._extract_profiles()

    def parse_profile(self, file_path: str) -> object:
        """
        Parse a build profile from the given file path and return the parsed object.
        Protocol method for BuildProfileParserProtocol.
        """
        parser = BuildProfileParser(file_path, resolver=self._resolver)
        return parser

    def _load_json(self) -> dict[str, Any]:
        """
        Load and parse the build profile JSON file.

        Returns:
            dict[str, Any]: Loaded JSON object.

        Raises:
            ValueError: If the file cannot be parsed as JSON.
        """
        input_str = self._input
        try:
            if input_str.startswith("https://maxroll.gg/d3/guides/"):
                obj = self._load_from_guide_url(input_str)
            elif input_str.startswith("http://") or input_str.startswith("https://"):
                obj = self._load_from_remote_json(input_str)
            else:
                with self.file_path.open(encoding="utf-8") as f:
                    content = f.read()
                obj = json.loads(content)
        except BuildProfileError:
            raise
        except Exception as e:  # pragma: no cover - unexpected IO/JSON issues
            msg = f"Could not parse build profile JSON: {e}"
            raise BuildProfileError(msg, file_path=str(self.file_path)) from e
        if not isinstance(obj, dict):  # defensive
            msg = "Top level profile JSON must be an object."
            raise BuildProfileError(
                msg,
                file_path=str(self.file_path),
            )
        return cast("dict[str, Any]", obj)

    def _load_from_guide_url(self, guide_url: str) -> dict[str, Any]:
        if self._resolver is None:
            if self._config is not None:
                self._resolver = GuideProfileResolver(self._config)
            else:
                msg = "Guide URLs require a GuideProfileResolver"
                raise BuildProfileError(msg, file_path=guide_url)
        try:
            return self._resolver.resolve(guide_url)
        except BuildProfileError:
            raise
        except Exception as exc:  # pragma: no cover - network/IO
            msg = f"Could not fetch guide {guide_url}: {exc}"
            raise BuildProfileError(msg, file_path=guide_url) from exc

    def _load_from_remote_json(self, url: str) -> dict[str, Any]:
        obj: Any | None = None
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            try:
                obj = resp.json()
            except Exception:
                html = resp.text
                m = re.search(r"d3planner/(\d+)", html)
                if not m:
                    m = re.search(r"data-d3planner-id=\"(\d+)\"", html)
                if not m:
                    raise
                planner_id = m.group(1)
                asset_url = f"https://assets-ng.maxroll.gg/d3planner/{planner_id}.json"
                try:
                    resp2 = requests.get(asset_url, timeout=10)
                    resp2.raise_for_status()
                    obj = resp2.json()
                except Exception as e:  # pragma: no cover - network/IO issues
                    msg = f"Could not fetch/parse remote profile JSON (fallback): {e}"
                    raise BuildProfileError(msg, file_path=asset_url) from e
        except BuildProfileError:
            raise
        except Exception as e:  # pragma: no cover - network/IO issues
            msg = f"Could not fetch/parse remote profile JSON: {e}"
            raise BuildProfileError(msg, file_path=url) from e
        if not isinstance(obj, dict):
            msg = "Remote profile JSON must be an object."
            raise BuildProfileError(msg, file_path=url)
        return cast("dict[str, Any]", obj)

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
        return cast("dict[str, Any]", data)

    def _extract_profiles(self) -> list[BuildProfileData]:
        """
        Extract build profiles from the parsed build data.

        Returns:
            list[ProfileData]: List of extracted profiles.
        """
        profiles_raw_any = self.build_data.get("profiles", [])
        result: list[BuildProfileData] = []
        if not isinstance(profiles_raw_any, list):  # defensive
            msg = "'profiles' must be a list if present."
            raise BuildProfileError(msg, file_path=str(self.file_path))
        profiles_raw = cast("list[object]", profiles_raw_any)
        for idx, profile_obj in enumerate(profiles_raw):
            if not isinstance(profile_obj, dict):  # skip invalid entries
                continue
            profile_dict = cast("dict[str, Any]", profile_obj)
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
        profiles_raw_any = self.build_data.get("profiles", [])
        if not isinstance(profiles_raw_any, list):
            return []
        profiles_raw = cast("list[object]", profiles_raw_any)

        def parse_slot(slot: str) -> ItemSlot:
            try:
                return ItemSlot(slot)
            except ValueError:
                return ItemSlot.OTHER

        def extract_main_items(
            profile_dict: dict[str, Any], profile_name: str
        ) -> list[BuildProfileItems]:
            items_value = profile_dict.get("items", {})
            usages: list[BuildProfileItems] = []
            if isinstance(items_value, dict):
                items = cast("dict[str, Any]", items_value)
                for slot_obj, item_obj in items.items():
                    slot_str = str(slot_obj)
                    slot_enum = parse_slot(slot_str)
                    item_id: Any | None = None
                    if isinstance(item_obj, dict):
                        item_dict = cast("dict[str, Any]", item_obj)
                        item_id = item_dict.get("id")
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
            kanai_value = profile_dict.get("kanai", {})
            usages: list[BuildProfileItems] = []
            if isinstance(kanai_value, dict):
                kanai = cast("dict[str, Any]", kanai_value)
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
            follower_items_value = profile_dict.get("followerItems", {})
            usages: list[BuildProfileItems] = []
            if isinstance(follower_items_value, dict):
                follower_items = cast("dict[str, Any]", follower_items_value)
                for slot_obj, raw_item in follower_items.items():
                    slot_enum = parse_slot(str(slot_obj))
                    item_id: Any | None
                    if isinstance(raw_item, dict):
                        raw_item_dict = cast("dict[str, Any]", raw_item)
                        item_id = raw_item_dict.get("id")
                    elif isinstance(raw_item, str):
                        item_id = raw_item
                    else:
                        item_id = None
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
        for profile_obj in profiles_raw:
            if not isinstance(profile_obj, dict):
                continue
            profile_dict = cast("dict[str, Any]", profile_obj)
            profile_name = str(profile_dict.get("name", ""))
            item_usages.extend(extract_main_items(profile_dict, profile_name))
            item_usages.extend(extract_kanai_items(profile_dict, profile_name))
            item_usages.extend(extract_follower_items(profile_dict, profile_name))
        return item_usages
