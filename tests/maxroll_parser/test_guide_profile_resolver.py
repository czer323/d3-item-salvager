"""Tests for GuideProfileResolver covering HTML parsing and payload merging."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from unittest.mock import ANY

import pytest
import requests

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.maxroll_parser.guide_profile_resolver import GuideProfileResolver
from d3_item_salvager.maxroll_parser.maxroll_exceptions import BuildProfileError

if TYPE_CHECKING:  # pragma: no cover - typing only
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
    ) -> None:
        self.text = text
        self._json_data = json_data
        self.status_code = status_code

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

    resolver = GuideProfileResolver(AppConfig(), session=session)
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

    resolver = GuideProfileResolver(AppConfig(), session=session)
    with pytest.raises(BuildProfileError, match="planner IDs"):
        resolver.resolve("https://maxroll.gg/d3/guides/missing-ids")
