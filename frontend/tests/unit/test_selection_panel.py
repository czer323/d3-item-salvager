"""Failing unit tests for the selection panel UI (T008a).

These tests assert the presence and basic structure of the new selection panel
and collapsed summary partials. They are intentionally written to fail until the
corresponding templates and JS are implemented.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


def test_dashboard_shows_selection_panel_when_no_builds_selected(
    client: FlaskClient,
) -> None:
    """When no build_ids are provided, the full selection panel should be visible."""
    resp = client.get("/")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data, "html.parser")

    # Expect a panel container for selection controls (to be implemented)
    panel = soup.select_one("#selection-panel")
    assert panel is not None, (
        "Expected '#selection-panel' to be present on the dashboard"
    )


def test_dashboard_shows_summary_when_builds_selected(frontend_app: Flask) -> None:
    """When build_ids are provided, the selection UI should appear as a collapsed summary."""

    # Patch the selection view builder to return a view with selected builds
    class _StubView:
        selected_build_ids = ("1",)
        selected_class_ids = ("Barbarian",)

    # Render the selection_panel template directly with a stubbed view to avoid backend wiring
    with frontend_app.test_request_context("/?build_ids=1"):
        html = frontend_app.jinja_env.get_template("selection_panel.html").render(
            selection_view=_StubView(), selection_collapsed=True
        )
    soup = BeautifulSoup(html, "html.parser")

    summary = soup.select_one("#selection-summary")
    assert summary is not None, (
        "Expected '#selection-summary' to be present when builds are selected"
    )
    # The summary should include an Edit affordance
    edit_btn = summary.select_one("[data-testid='selection-edit-button']")
    assert edit_btn is not None, "Expected an Edit affordance in the selection summary"
