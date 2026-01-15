"""Unit tests for items summary partial rendering (regression test for frontend_config availability)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
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
