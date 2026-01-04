"""Failing tests for keyboard accessibility of selection flows (T010a).

Focus on presence of keyboard-accessible affordances and ARIA attributes. JS-driven keyboard behavior will be covered in e2e tests later; unit tests ensure the markup is ready for keyboard control.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


def test_edit_affordance_is_keyboard_focusable(frontend_app: Flask) -> None:
    class _StubView:
        selected_build_ids = ("1",)

    with frontend_app.test_request_context("/?build_ids=1"):
        html = frontend_app.jinja_env.get_template("selection_panel.html").render(
            selection_view=_StubView(), selection_collapsed=True
        )
    soup = BeautifulSoup(html, "html.parser")

    edit = soup.select_one("[data-testid='selection-edit-button']")
    assert edit is not None

    # Ensure the affordance can be focused and has appropriate role
    assert edit.get("role") in ("button", None)
    assert edit.get("tabindex") in ("0", "")


def test_apply_button_is_triggerable_via_keyboard(client: FlaskClient) -> None:
    # The Apply control should be a submit-type button (keyboard triggers submit)
    resp = client.get("/")
    soup = BeautifulSoup(resp.data, "html.parser")

    apply_btn = soup.select_one("[data-testid='apply-filter-button']")
    assert apply_btn is not None
    assert apply_btn.name == "button"
    assert apply_btn.get("type") == "submit" or apply_btn.get("role") == "button"
