"""Frontend application entrypoint for the d3-item-salvager UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    msg = "App factory not implemented yet"
    raise NotImplementedError(msg)
