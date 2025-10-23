"""Base routes for core frontend pages."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import Blueprint, current_app, render_template

if TYPE_CHECKING:
    from frontend.src.config import FrontendConfig

base_blueprint = Blueprint("pages", __name__)


@base_blueprint.get("/")
def dashboard() -> str:
    """Render the dashboard placeholder view."""
    config = cast("FrontendConfig", current_app.config["FRONTEND_CONFIG"])
    return render_template(
        "pages/dashboard.html",
        page_title="D3 Item Salvager",
        frontend_config=config,
    )
