"""Failing unit tests for the item row template (T018a).

These tests assert that an item row partial exists and renders the expected
name, ARIA-label and usage chips. They are intentionally failing until the
template is implemented.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask


def test_item_row_template_renders_name_and_aria(frontend_app: Flask) -> None:
    item = SimpleNamespace(
        id="item-1",
        name="Mighty Weapon",
        quality="Set",
        slot="Weapon",
        usage_contexts=("main",),
    )

    with frontend_app.test_request_context("/"):
        html = frontend_app.jinja_env.get_template("item_row.html").render(item=item)

    soup = BeautifulSoup(html, "html.parser")
    row = soup.select_one(".item-row")
    assert row is not None, "Expected '.item-row' root element in 'item_row.html'"

    name_el = row.select_one(".item-name")
    assert name_el is not None, "Expected element with class 'item-name'"
    aria = name_el.get("aria-label")
    assert aria is not None, "Expected name element to include an ARIA label"
    assert "Mighty Weapon" in aria, "Expected ARIA label to contain the item name"


def test_item_row_renders_usage_chips(frontend_app: Flask) -> None:
    item = SimpleNamespace(
        id="item-2",
        name="Traveler's Pledge",
        quality="Legendary",
        slot="Amulet",
        usage_contexts=("main", "follower"),
    )

    with frontend_app.test_request_context("/"):
        html = frontend_app.jinja_env.get_template("item_row.html").render(item=item)

    soup = BeautifulSoup(html, "html.parser")
    chips = [el.get_text(strip=True) for el in soup.select(".usage-chip")]
    assert "main" in chips, "Expected 'main' usage chip to be present"
    assert "follower" in chips, "Expected 'follower' usage chip to be present"
