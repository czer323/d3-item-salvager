"""Utilities for resolving Maxroll build guide pages into planner profile payloads."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from threading import Lock
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
        self._max_retries: int = mp_cfg.planner_retry_attempts
        self._backoff: float = mp_cfg.planner_retry_backoff
        self._retry_statuses: set[int] = set(mp_cfg.planner_retry_status_codes)
        self._min_interval: float = mp_cfg.planner_request_interval
        self._cache_enabled: bool = mp_cfg.planner_cache_enabled
        self._cache_dir: Path = Path(mp_cfg.planner_cache_dir)
        self._cache_ttl: int = mp_cfg.planner_cache_ttl
        self._request_lock = Lock()
        self._last_request_at: float = 0.0
        if self._cache_enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._html_headers = {
            "User-Agent": self._user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self._json_headers = {
            "User-Agent": self._user_agent,
            "Accept": "application/json",
        }

    def resolve(self, guide_url: str) -> dict[str, Any]:
        """Return a combined build profile payload for the given guide URL.

        NOTE: some guide pages embed multiple planner payloads. Historically the
        resolver combined profiles from all planner payloads into a single
        payload; that behaviour is preserved for compatibility. Downstream
        callers are encouraged to call `get_planner_ids()` and fetch planner
        payloads individually when separate builds are desired.
        """
        planner_ids = self._extract_planner_ids(guide_url)
        if not planner_ids:
            msg = "Guide did not embed any planner IDs."
            raise BuildProfileError(
                msg,
                file_path=guide_url,
                context={"guide_url": guide_url},
            )

        bundles: list[_ResponseBundle] = []
        for planner_id in planner_ids:
            try:
                payload = self._fetch_planner_payload(planner_id)
            except BuildProfileError:
                raise
            except Exception as exc:  # pragma: no cover - network/IO failures
                url = self._profile_url_template.format(planner_id=planner_id)
                msg = f"Failed to load planner profile {planner_id}: {exc}"
                raise BuildProfileError(
                    msg,
                    file_path=url,
                    context={"planner_id": planner_id},
                ) from exc
            bundles.append(_ResponseBundle(planner_id=planner_id, payload=payload))

        if not bundles:
            msg = "Guide did not yield any valid planner payloads."
            raise BuildProfileError(
                msg,
                file_path=guide_url,
                context={"guide_url": guide_url},
            )

        return self._combine_payloads(bundles)

    def get_planner_ids(self, guide_url: str) -> list[str]:
        """Return planner IDs embedded in the guide page.

        This is a public wrapper around the extraction logic used internally by
        :meth:`resolve`. Callers may use this to split multi-planner guides into
        separate processing units (one per planner ID) instead of combining
        profiles into a single build.
        """
        return self._extract_planner_ids(guide_url)

    # ------------------------------------------------------------------
    def _extract_planner_ids(self, guide_url: str) -> list[str]:
        self._respect_request_interval()
        response = self._session.get(
            guide_url, headers=self._html_headers, timeout=self._timeout
        )
        response.raise_for_status()
        html = response.text
        candidates: list[str] = []
        seen: set[str] = set()

        # Prefer explicit data-d3planner-id attributes but exclude ids that are
        # clearly associated with 'non-profile' elements like altars.
        # Example: <div ... data-d3planner-id="315680726" data-d3planner-type="altar" ...>
        blacklist_types = {"altar"}
        # Find tags that contain data-d3planner-id and inspect for type inside tag
        tag_pattern = re.compile(
            r"<[^>]*\bdata-d3planner-id=[\'\"](\d+)[\'\"][^>]*>",
            re.IGNORECASE | re.DOTALL,
        )
        for m in tag_pattern.finditer(html):
            pid = m.group(1)
            tag = m.group(0)
            type_m = re.search(
                r"\bdata-d3planner-type=[\'\"]([^\'\"]+)[\'\"]", tag, re.IGNORECASE
            )
            if type_m and type_m.group(1).lower() in blacklist_types:
                # skip altar/planner types that are not actual build profiles
                continue
            if pid not in seen:
                candidates.append(pid)
                seen.add(pid)

        # Fallback: URLs that reference planner ids (e.g., /d3planner/123) - only
        # include if not seen already.
        for value in re.findall(r"/d3planner/(\d+)", html):
            if value not in seen:
                candidates.append(value)
                seen.add(value)

        return candidates

    def _fetch_planner_payload(self, planner_id: str) -> dict[str, Any]:
        url = self._profile_url_template.format(planner_id=planner_id)
        cached = self._load_cached_payload(planner_id)
        if cached is not None:
            return cached

        attempt = 1
        while True:
            self._respect_request_interval()
            try:
                # Use a short connect timeout to avoid long SSL/connect hangs and a
                # longer read timeout for payload download.
                timeout_val = (3.0, self._timeout)
                response = self._session.get(
                    url, headers=self._json_headers, timeout=timeout_val
                )
            except Exception as exc:
                msg = f"Failed to fetch planner payload (network error): {exc}"
                raise BuildProfileError(
                    msg, file_path=url, context={"planner_id": planner_id}
                ) from exc

            if response.status_code < 400:
                data = response.json()
                if not isinstance(data, dict):
                    msg = "Planner response must be a JSON object."
                    raise BuildProfileError(
                        msg,
                        file_path=url,
                        context={"planner_id": planner_id},
                    )
                typed = cast("dict[str, Any]", data)
                self._store_cached_payload(planner_id, typed)
                return typed

            if (
                attempt >= self._max_retries
                or response.status_code not in self._retry_statuses
            ):
                response.raise_for_status()

            wait_for = self._calculate_retry_wait(response, attempt)
            self._sleep(wait_for)
            attempt += 1

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

    def _load_cached_payload(self, planner_id: str) -> dict[str, Any] | None:
        if not self._cache_enabled:
            return None
        cache_file = self._cache_dir / f"{planner_id}.json"
        if not cache_file.exists():
            return None
        if self._cache_ttl:
            expiry = cache_file.stat().st_mtime + self._cache_ttl
            if time.time() >= expiry:
                return None
        try:
            with cache_file.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover - I/O issue
            msg = f"Planner cache file {cache_file} could not be read: {exc}"
            raise BuildProfileError(
                msg,
                file_path=str(cache_file),
                context={"planner_id": planner_id},
            ) from exc
        if not isinstance(data, dict):
            return None
        return cast("dict[str, Any]", data)

    def _store_cached_payload(self, planner_id: str, payload: dict[str, Any]) -> None:
        if not self._cache_enabled:
            return
        cache_file = self._cache_dir / f"{planner_id}.json"
        try:
            temp_path = cache_file.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            temp_path.replace(cache_file)
        except OSError:  # pragma: no cover - unexpected OS failures
            return

    def _respect_request_interval(self) -> None:
        if self._min_interval <= 0:
            return
        while True:
            with self._request_lock:
                now = time.monotonic()
                elapsed = now - self._last_request_at
                if elapsed >= self._min_interval:
                    self._last_request_at = now
                    return
                wait_time = self._min_interval - elapsed
            self._sleep(wait_time)

    def _calculate_retry_wait(
        self,
        response: requests.Response,
        attempt: int,
    ) -> float:
        header_wait = self._parse_retry_after(response.headers.get("Retry-After"))
        if header_wait is not None:
            return max(0.0, header_wait)
        exponent = max(attempt - 1, 0)
        wait = self._backoff**exponent
        return max(wait, self._min_interval)

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            try:
                parsed = parsedate_to_datetime(value)
            except (TypeError, ValueError):
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            delta = (parsed - datetime.now(tz=UTC)).total_seconds()
            return max(delta, 0.0)

    @staticmethod
    def _sleep(seconds: float) -> None:
        if seconds <= 0:
            return
        time.sleep(seconds)
