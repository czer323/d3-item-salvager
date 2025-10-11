"""Utilities for resolving Maxroll build guide pages into planner profile payloads."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import requests

from .maxroll_exceptions import BuildProfileError

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterable

    from requests import Session

    from d3_item_salvager.config.settings import AppConfig


@dataclass(slots=True)
class _ResponseBundle:
    """Small helper container for storing planner payloads and derived metadata."""

    planner_id: str
    payload: dict[str, Any]


class GuideProfileResolver:
    """Fetch planner profile payloads for a given Maxroll guide URL."""

    def __init__(
        self,
        config: AppConfig,
        *,
        session: Session | None = None,
    ) -> None:
        self._config = config
        self._session: Session = session or requests.Session()
        mp_cfg = config.maxroll_parser
        self._profile_url_template: str = mp_cfg.planner_profile_url
        self._timeout: float = mp_cfg.planner_request_timeout
        self._user_agent: str = mp_cfg.planner_user_agent
        self._html_headers = {
            "User-Agent": self._user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self._json_headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }

    def resolve(self, guide_url: str) -> dict[str, Any]:
        """Return a combined build profile payload for the given guide URL."""
        planner_ids = self._extract_planner_ids(guide_url)
        if not planner_ids:
            msg = "Guide did not embed any planner IDs."
            raise BuildProfileError(msg, file_path=guide_url)

        bundles: list[_ResponseBundle] = []
        for planner_id in planner_ids:
            try:
                payload = self._fetch_planner_payload(planner_id)
            except BuildProfileError:
                raise
            except Exception as exc:  # pragma: no cover - network/IO failures
                url = self._profile_url_template.format(planner_id=planner_id)
                msg = f"Failed to load planner profile {planner_id}: {exc}"
                raise BuildProfileError(msg, file_path=url) from exc
            bundles.append(_ResponseBundle(planner_id=planner_id, payload=payload))

        if not bundles:
            msg = "Guide did not yield any valid planner payloads."
            raise BuildProfileError(msg, file_path=guide_url)

        return self._combine_payloads(bundles)

    # ------------------------------------------------------------------
    def _extract_planner_ids(self, guide_url: str) -> list[str]:
        response = self._session.get(
            guide_url, headers=self._html_headers, timeout=self._timeout
        )
        response.raise_for_status()
        html = response.text
        candidates: list[str] = []
        seen: set[str] = set()

        attr_matches = re.findall(r"data-d3planner-id=\"(\d+)\"", html)
        attr_matches.extend(re.findall(r"data-d3planner-id='(\d+)'", html))
        url_matches = re.findall(r"/d3planner/(\d+)", html)

        for value in attr_matches + url_matches:
            if value not in seen:
                candidates.append(value)
                seen.add(value)
        return candidates

    def _fetch_planner_payload(self, planner_id: str) -> dict[str, Any]:
        url = self._profile_url_template.format(planner_id=planner_id)
        response = self._session.get(
            url, headers=self._json_headers, timeout=self._timeout
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            msg = "Planner response must be a JSON object."
            raise BuildProfileError(msg, file_path=url)
        return cast("dict[str, Any]", data)

    def _combine_payloads(self, bundles: Iterable[_ResponseBundle]) -> dict[str, Any]:
        combined_profiles: list[Any] = []
        base_payload: dict[str, Any] | None = None
        base_data: dict[str, Any] | None = None

        for bundle in bundles:
            payload = bundle.payload
            data_field = payload.get("data")
            data_dict = self._ensure_dict(data_field, bundle.planner_id)
            profiles_field = data_dict.get("profiles")
            if isinstance(profiles_field, list):
                combined_profiles.extend(cast("list[Any]", profiles_field))
            if base_payload is None:
                base_payload = dict(payload)
                base_data = data_dict

        if base_payload is None or base_data is None:
            msg = "Planner payloads did not contain usable data."
            raise BuildProfileError(msg, file_path="planner")

        base_data = dict(base_data)
        base_data["profiles"] = combined_profiles
        base_payload["data"] = base_data
        return base_payload

    @staticmethod
    def _ensure_dict(value: object, planner_id: str) -> dict[str, Any]:
        if isinstance(value, dict):
            return cast("dict[str, Any]", value)
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                msg = f"Planner {planner_id} returned unparsable data field."
                raise BuildProfileError(msg, file_path=planner_id) from exc
            if isinstance(parsed, dict):
                return cast("dict[str, Any]", parsed)
        msg = "Planner payload missing JSON object under 'data'."
        raise BuildProfileError(msg, file_path=planner_id)
