"""Failing tests for search result affordances (T016a).

These assert that the search partial provides a suggestion template with action
buttons that client-side JS can clone and use for each suggestion.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from flask import Flask


def test_search_includes_lookup_status(
    frontend_app: Flask, frontend_config: SimpleNamespace
) -> None:
    """The filter controls should expose the status element for lookup feedback."""
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
    assert status is not None, "Expected a search status message container"
