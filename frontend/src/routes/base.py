"""Base routes for core frontend pages."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import Blueprint, current_app, g, render_template, request

from frontend.src.services.backend_client import BackendClient, BackendClientError
from frontend.src.services.variant_summary import VariantSummary, build_variant_summary

if TYPE_CHECKING:
    from frontend.src.config import FrontendConfig

base_blueprint = Blueprint("pages", __name__)


@base_blueprint.get("/")
def dashboard() -> str:
    """Render the dashboard placeholder view."""
    config = cast("FrontendConfig", current_app.config["FRONTEND_CONFIG"])
    variant_summary: VariantSummary | None = None
    summary_error: str | None = None

    target_variant = request.args.get("variant") or config.default_variant_ids[0]
    client = cast("BackendClient | None", getattr(g, "backend_client", None))

    if client is not None:
        try:
            variant_summary = build_variant_summary(client, target_variant)
        except BackendClientError as exc:
            summary_error = str(exc)

    return render_template(
        "pages/dashboard.html",
        page_title="D3 Item Salvager",
        frontend_config=config,
        variant_summary=variant_summary,
        summary_error=summary_error,
    )
