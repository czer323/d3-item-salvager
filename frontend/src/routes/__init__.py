"""Routing entrypoints for the frontend application."""

from flask import Flask

from frontend.src.routes.base import base_blueprint
from frontend.src.routes.items import items_blueprint
from frontend.src.routes.selection import selection_blueprint
from frontend.src.routes.variants import variants_blueprint

BLUEPRINTS = (
    base_blueprint,
    items_blueprint,
    selection_blueprint,
    variants_blueprint,
)


def register_blueprints(app: Flask) -> None:
    """Register all blueprints with the provided Flask app."""
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)


__all__ = ["BLUEPRINTS", "register_blueprints"]
