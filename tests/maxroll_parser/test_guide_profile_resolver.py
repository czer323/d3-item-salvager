"""Tests for GuideProfileResolver covering HTML parsing and payload merging."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import ANY

import pytest
import requests

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.maxroll_parser.guide_profile_resolver import GuideProfileResolver
from d3_item_salvager.maxroll_parser.maxroll_exceptions import BuildProfileError

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping
    from pathlib import Path

    from pytest_mock import MockerFixture
else:

    class MockerFixture:  # pragma: no cover - runtime placeholder
        pass


class _FakeResponse:
    """Minimal response double for requests.Session.get."""

    def __init__(
        self,
        *,
        text: str = "",
        json_data: dict[str, Any] | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.text = text
        self._json_data = json_data
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            message = f"HTTP {self.status_code}"
            raise requests.HTTPError(message)

    def json(self) -> dict[str, Any]:
        if self._json_data is None:
            message = "No JSON data available"
            raise ValueError(message)
        return self._json_data


def _html_with_ids() -> str:
    return (
        '<div data-d3planner-id="123"></div>'
        "<script>var link='https://planners.maxroll.gg/d3planner/456';</script>"
    )


def _resolver_config(overrides: Mapping[str, object] | None = None) -> AppConfig:
    base_overrides: dict[str, object] = {
        "planner_request_interval": 0.0,
        "planner_cache_enabled": False,
    }
    if overrides:
        base_overrides.update(overrides)
    config = AppConfig()
    config.maxroll_parser = config.maxroll_parser.model_copy(update=base_overrides)
    return config


def test_resolver_merges_profiles(mocker: MockerFixture) -> None:
    """Resolver should fetch all planner payloads and merge their profiles."""
    session = mocker.create_autospec(requests.Session, instance=True)
    html_response = _FakeResponse(text=_html_with_ids())
    payload_one = {"data": {"profiles": [{"name": "A", "class": "wizard"}]}}
    payload_two = {"data": {"profiles": [{"name": "B", "class": "barbarian"}]}}

    responses = iter(
        [
            html_response,
            _FakeResponse(json_data=payload_one),
            _FakeResponse(json_data=payload_two),
        ]
    )

    def _next_response(*_: object, **__: object) -> _FakeResponse:
        return next(responses)

    session.get.side_effect = _next_response

    resolver = GuideProfileResolver(_resolver_config(), session=session)
    result = resolver.resolve("https://maxroll.gg/d3/guides/sample-guide")

    data = result["data"]
    assert isinstance(data, dict)
    data_dict = cast("dict[str, Any]", data)
    profiles_raw = cast("list[Any]", data_dict.get("profiles", []))
    names = [cast("dict[str, Any]", profile).get("name") for profile in profiles_raw]
    assert names == ["A", "B"]

    session.get.assert_any_call(  # type: ignore[no-untyped-call]
        "https://maxroll.gg/d3/guides/sample-guide",
        headers=ANY,
        timeout=ANY,
    )
    session.get.assert_any_call(  # type: ignore[no-untyped-call]
        "https://planners.maxroll.gg/profiles/load/d3/123",
        headers=ANY,
        timeout=ANY,
    )


def test_resolver_requires_planner_ids(mocker: MockerFixture) -> None:
    """Resolver raises when no planner IDs can be derived from the guide HTML."""
    session = mocker.create_autospec(requests.Session, instance=True)
    session.get.return_value = _FakeResponse(
        text="<html><body>No ids here</body></html>"
    )

    resolver = GuideProfileResolver(_resolver_config(), session=session)
    with pytest.raises(BuildProfileError, match="planner IDs"):
        resolver.resolve("https://maxroll.gg/d3/guides/missing-ids")


def test_resolver_retries_on_rate_limit(mocker: MockerFixture) -> None:
    """Resolver should retry planner payload fetches when the API returns 429."""
    session = mocker.create_autospec(requests.Session, instance=True)
    html_response = _FakeResponse(text='<div data-d3planner-id="123"></div>')
    rate_limited = _FakeResponse(status_code=429, headers={"Retry-After": "1"})
    payload: dict[str, dict[str, list[dict[str, str]]]] = {
        "data": {"profiles": [{"name": "Retry", "class": "monk"}]}
    }
    success_response = _FakeResponse(json_data=payload)

    session.get.side_effect = [html_response, rate_limited, success_response]
    sleep_mock = mocker.patch(
        "d3_item_salvager.maxroll_parser.guide_profile_resolver.GuideProfileResolver._sleep",
        return_value=None,
    )

    resolver = GuideProfileResolver(
        _resolver_config({"planner_retry_attempts": 2}),
        session=session,
    )
    result = resolver.resolve("https://maxroll.gg/d3/guides/sample-guide")

    assert result == payload
    assert session.get.call_count == 3
    sleep_mock.assert_called()


def test_resolver_uses_cached_payload(tmp_path: Path, mocker: MockerFixture) -> None:
    """Resolver should read cached planner payloads instead of refetching."""
    session = mocker.create_autospec(requests.Session, instance=True)
    html_response = _FakeResponse(text='<div data-d3planner-id="123"></div>')
    session.get.side_effect = [html_response]

    cache_dir = tmp_path / "planner"
    cache_dir.mkdir()
    cached_payload = {"data": {"profiles": [{"name": "Cached", "class": "monk"}]}}
    (cache_dir / "123.json").write_text(json.dumps(cached_payload), encoding="utf-8")

    resolver = GuideProfileResolver(
        _resolver_config(
            {
                "planner_cache_enabled": True,
                "planner_cache_dir": str(cache_dir),
            }
        ),
        session=session,
    )
    result = resolver.resolve("https://maxroll.gg/d3/guides/sample-guide")

    assert result == cached_payload
    assert session.get.call_count == 1
