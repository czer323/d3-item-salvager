"""Failing unit tests for the item list template and client wiring (T011a).

These tests assert that the `item_list.html` partial exists and contains the
expected root element where items will be rendered. They are intentionally
written to fail until `frontend/templates/item_list.html` and supporting JS
are implemented.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask


def test_item_list_template_exists(frontend_app: Flask) -> None:
    """The `item_list.html` template should exist and expose a container with id `item-list`."""
    # Rendering directly via Jinja to avoid full browser testing at this stage
    html = frontend_app.jinja_env.get_template("item_list.html").render()
    soup = BeautifulSoup(html, "html.parser")

    container = soup.select_one("#item-list")
    assert container is not None, (
        "Expected '#item-list' to be present in 'item_list.html' template"
    )


def test_item_list_template_has_virtual_list_hook(frontend_app: Flask) -> None:
    """The template should include a hook for client-side virtualization (data-virtual-list)."""
    html = frontend_app.jinja_env.get_template("item_list.html").render()
    soup = BeautifulSoup(html, "html.parser")

    hook = soup.select_one("[data-virtual-list]")
    assert hook is not None, (
        "Expected a 'data-virtual-list' hook in 'item_list.html' for virtualization"
    )
