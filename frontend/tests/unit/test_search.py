"""Unit tests for basic search wiring and markup (T017a).

These tests assert the presence of the client-side script and the suggestion
template structure. They are intentionally small and focused so clients can be
implemented iteratively.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from types import SimpleNamespace

    from flask import Flask
    from flask.testing import FlaskClient


def test_search_script_included_on_dashboard(client: FlaskClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "search.js" in html, "Expected search.js to be included on the dashboard"


def test_lookup_status_present(
    frontend_app: Flask, frontend_config: SimpleNamespace
) -> None:
    # Render the component directly to reliably locate the status indicator
    from types import SimpleNamespace

    summary = SimpleNamespace(filters=SimpleNamespace(search=""), available_slots=[])
    with frontend_app.test_request_context("/"):
        html = frontend_app.jinja_env.get_template(
            "components/filter_controls.html"
        ).render(
            summary=summary,
            frontend_config=frontend_config,
        )

    soup = BeautifulSoup(html, "html.parser")
    status = soup.select_one("[data-testid='search-status']")
    assert status is not None, "Expected the lookup status element to be present"
