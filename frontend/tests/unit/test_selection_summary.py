"""Failing tests for the selection summary bar (T009a).

These tests assert that the collapsed summary includes labels for selected
classes/builds and an accessible Edit affordance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask


def test_summary_displays_selected_builds_and_edit_button(frontend_app: Flask) -> None:
    # Render the template directly with the stubbed view
    class _StubView:
        selected_build_ids = ("1", "3")
        selected_class_ids = ("Barbarian",)

    with frontend_app.test_request_context("/?build_ids=1&build_ids=3"):
        html = frontend_app.jinja_env.get_template("selection_panel.html").render(
            selection_view=_StubView()
        )
    soup = BeautifulSoup(html, "html.parser")

    summary = soup.select_one("#selection-summary")
    assert summary is not None

    # Expect a short text summary of selections
    text = summary.get_text(strip=True)
    assert "1" in text
    assert "3" in text

    # Edit affordance with accessible attributes
    edit = summary.select_one("[data-testid='selection-edit-button']")
    assert edit is not None
    assert edit.get("aria-controls") == "selection-panel"
    assert edit.get("tabindex") in ("0", "")
