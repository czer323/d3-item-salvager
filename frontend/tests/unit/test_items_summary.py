"""Unit tests for items summary partial rendering (regression test for frontend_config availability)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


@pytest.mark.usefixtures("patched_build_usage_table", "with_frontend_config")
def test_summary_partial_renders_with_frontend_config(client: FlaskClient) -> None:
    """Ensure the summary partial renders filter controls when config is provided."""
    resp = client.post("/frontend/items/summary", data={})
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "data-filter-controls" in html, (
        "Expected filter controls to be present in rendered summary"
    )

    # Sort button and attributes should be rendered on the Item header
    # Rows should include the expected data attributes for client-side filtering and identification
    assert "data-filter-item" in html
    assert "data-item-name" in html


@pytest.mark.usefixtures("patched_build_usage_table", "no_frontend_config")
def test_summary_partial_handles_missing_frontend_config(
    client: FlaskClient,
) -> None:
    """Ensure the summary partial still renders when the frontend config is missing."""
    resp = client.post("/frontend/items/summary", data={})
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "data-filter-controls" in html, (
        "Expected filter controls to be present in rendered summary even without FRONTEND_CONFIG"
    )


def test_summary_template_hides_slot_header_and_preserves_data_slot(
    frontend_app: Flask,
) -> None:
    # Construct a minimal table object expected by the template
    row = SimpleNamespace(
        item_id="item-1",
        name="Mighty Weapon",
        slot="Weapon",
        badge_class="badge-success",
        usage_contexts=("main", "follower"),
        variant_ids=("v1", "v2"),
    )
    table = SimpleNamespace(
        rows=[row],
        filters=SimpleNamespace(search="", slot=""),
        pagination=SimpleNamespace(page_size=20),
        total_items=1,
        used_total=1,
    )

    with frontend_app.test_request_context("/"):
        html = frontend_app.jinja_env.get_template("items/summary.html").render(
            table=table,
            frontend_config=SimpleNamespace(backend_base_url="http://127.0.0.1:8000"),
        )

    soup = BeautifulSoup(html, "html.parser")

    # The table header should not contain 'Slot'
    headers = [th.get_text(strip=True) for th in soup.select("thead th")]
    assert "Slot" not in headers

    # Row should retain data-item-slot attribute (lowercased)
    first_row = soup.select_one("tbody tr[data-filter-item]")
    assert first_row is not None
    assert first_row.get("data-item-slot") == "weapon"

    # Usage chips should be present with human-readable text and ordered
    chips = [el.get_text(strip=True) for el in first_row.select(".usage-chip")]
    assert chips == ["Main", "Follower"]


def test_summary_template_renders_empty_usage_fallback(frontend_app: Flask) -> None:
    # Construct a minimal table object with no usage_contexts
    row = SimpleNamespace(
        item_id="item-7",
        name="Strange Item",
        slot="Unknown",
        badge_class="badge-success",
        usage_contexts=(),
        variant_ids=(),
    )
    table = SimpleNamespace(
        rows=[row],
        filters=SimpleNamespace(search="", slot=""),
        pagination=SimpleNamespace(page_size=20),
        total_items=1,
        used_total=0,
    )

    with frontend_app.test_request_context("/"):
        html = frontend_app.jinja_env.get_template("items/summary.html").render(
            table=table,
            frontend_config=SimpleNamespace(backend_base_url="http://127.0.0.1:8000"),
        )

    soup = BeautifulSoup(html, "html.parser")
    first_row = soup.select_one("tbody tr[data-filter-item]")
    assert first_row is not None

    # Fallback visible em-dash should be present
    usage_cell = first_row.select_one("td .text-xs")
    assert usage_cell is not None
    assert "—" in usage_cell.get_text()

    # Screen-reader-only message should be present
    sr = usage_cell.select_one(".sr-only")
    assert sr is not None
    assert sr.get_text(strip=True) == "No usages"
