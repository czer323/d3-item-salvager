"""Failing unit tests for the virtualized list component (T013a).

These tests expect a `virtual_list.js` component and corresponding template hook.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask


def test_virtual_list_component_exists() -> None:
    path = (
        Path(__file__).resolve().parents[2] / "src" / "components" / "virtual_list.js"
    )
    assert path.exists(), f"Expected virtual list component at {path}"


def test_item_list_template_has_virtual_hook(frontend_app: Flask) -> None:
    html = frontend_app.jinja_env.get_template("item_list.html").render()
    soup = BeautifulSoup(html, "html.parser")

    hook = soup.select_one("[data-virtual-list]")
    assert hook is not None, "Expected 'data-virtual-list' hook in item_list template"
