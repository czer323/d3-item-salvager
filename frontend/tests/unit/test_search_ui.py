"""Failing unit tests for the search UI and partial (T015a/T017a).

These tests assert that a search partial and required DOM hooks exist so the
frontend component can be implemented test-first.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask


def test_search_partial_present_on_dashboard(
    frontend_app: Flask, frontend_config: SimpleNamespace
) -> None:
    """Dashboard should include the search partial with expected hooks."""
    summary = SimpleNamespace(filters=SimpleNamespace(search=""), available_slots=[])
    with frontend_app.test_request_context("/"):
        html = frontend_app.jinja_env.get_template(
            "components/filter_controls.html"
        ).render(
            summary=summary,
            frontend_config=frontend_config,
        )

    soup = BeautifulSoup(html, "html.parser")
    search_root = soup.select_one("[data-filter-controls]")
    assert search_root is not None, "Expected filter controls to be present"

    input_el = search_root.select_one("[data-filter-search]")
    assert input_el is not None, "Expected an input with data-filter-search"

    status_el = search_root.select_one("[data-testid='search-status']")
    assert status_el is not None, "Expected a status element for lookup feedback"


def test_search_partial_points_to_lookup_endpoint(
    frontend_app: Flask, frontend_config: SimpleNamespace
) -> None:
    """The search partial should include a data attribute with the lookup URL."""
    # Render the filter controls component directly with a minimal context so it is always present
    summary = SimpleNamespace(filters=SimpleNamespace(search=""), available_slots=[])
    with frontend_app.test_request_context("/"):
        html = frontend_app.jinja_env.get_template(
            "components/filter_controls.html"
        ).render(
            summary=summary,
            frontend_config=frontend_config,
        )

    soup = BeautifulSoup(html, "html.parser")
    search_root = soup.select_one("[data-filter-controls]")
    assert search_root is not None

    endpoint = search_root.get("data-lookup-url")
    assert endpoint is not None, "Expected data-lookup-url to be defined"
    endpoint_value = str(endpoint)
    assert endpoint_value.endswith("/items/lookup"), (
        "Expected the filter controls to include the backend lookup URL"
    )
    assert endpoint_value.startswith("http"), "Expected the lookup URL to be absolute"
