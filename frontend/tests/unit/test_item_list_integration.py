"""Unit test to ensure item_list client script is included in dashboard (part of T011)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask.testing import FlaskClient


def test_dashboard_includes_item_list_script(client: FlaskClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data, "html.parser")

    scripts = [cast("str", s.get("src")) for s in soup.select("script") if s.get("src")]
    assert any("js/item_list.js" in src for src in scripts), (
        "Expected 'js/item_list.js' to be included on the dashboard"
    )
