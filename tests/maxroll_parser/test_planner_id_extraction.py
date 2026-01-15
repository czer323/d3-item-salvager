"""Tests for planner id extraction, ensuring altar types are excluded."""

from typing import Any

import requests

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.maxroll_parser.guide_profile_resolver import GuideProfileResolver


def test_exclude_altar_planner_ids(mocker: Any) -> None:  # noqa: ANN401
    html = (
        '<div class="d3planner-build" data-d3planner-id="315680726" data-d3planner-type="altar"></div>'
        '<div class="d3planner-build" data-d3planner-id="123456789"></div>'
        "<script>var link='https://planners.maxroll.gg/d3planner/456789012';</script>"
    )

    # Mock requests.Session.get to return our HTML
    session = mocker.create_autospec(requests.Session, instance=True)

    class _R:
        text: str = html
        status_code: int = 200

        def raise_for_status(self) -> None:
            return None

    session.get.return_value = _R()

    resolver = GuideProfileResolver(AppConfig(), session=session)
    ids = resolver.get_planner_ids("https://maxroll.gg/d3/guides/sample-guide")

    # Should exclude the altar id 315680726, but include 123456789 and 456789012
    assert "315680726" not in ids
    assert "123456789" in ids
    assert "456789012" in ids


def test_include_id_from_url_if_no_attrs(mocker: Any) -> None:  # noqa: ANN401
    html = "<script>somevar='https://planners.maxroll.gg/d3planner/999999999'</script>"
    session = mocker.create_autospec(requests.Session, instance=True)

    class _R:
        text: str = html
        status_code: int = 200

        def raise_for_status(self) -> None:
            return None

    session.get.return_value = _R()
    resolver = GuideProfileResolver(AppConfig(), session=session)
    ids = resolver.get_planner_ids("https://maxroll.gg/d3/guides/sample-guide")
    assert ids == ["999999999"]
