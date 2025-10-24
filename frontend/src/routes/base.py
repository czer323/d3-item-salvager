"""Base routes for core frontend pages."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import Blueprint, current_app, g, render_template, request

from frontend.src.services.backend_client import BackendClient, BackendClientError
from frontend.src.services.filtering import parse_page, parse_page_size
from frontend.src.services.preferences import compose_preferences, to_payload
from frontend.src.services.selection import build_selection_view
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
    selection_view = None
    selection_error: str | None = None

    requested_variant = request.args.get("variant") or config.default_variant_ids[0]
    requested_class = request.args.get("class_id")
    requested_build = request.args.get("build_id")
    search_term = request.args.get("search", "")
    slot_filter = request.args.get("slot")
    used_page = parse_page(request.args.get("used_page"), default=1)
    salvage_page = parse_page(request.args.get("salvage_page"), default=1)
    page_size = parse_page_size(request.args.get("page_size"))
    client = cast("BackendClient | None", getattr(g, "backend_client", None))

    if client is not None:
        try:
            selection_view = build_selection_view(
                client,
                default_variant_ids=config.default_variant_ids,
                class_id=requested_class,
                build_id=requested_build,
                variant_id=requested_variant,
            )
        except BackendClientError as exc:
            selection_error = str(exc)
        else:
            resolved_variant = selection_view.selected_variant_id or requested_variant
            if resolved_variant:
                try:
                    variant_summary = build_variant_summary(
                        client,
                        resolved_variant,
                        search=search_term,
                        slot=slot_filter,
                        used_page=used_page,
                        salvage_page=salvage_page,
                        page_size=page_size,
                    )
                except BackendClientError as exc:
                    summary_error = str(exc)
            else:
                summary_error = (
                    "No variant is currently available for the selected filters."
                )
    else:
        selection_error = "Backend client not available"

    target_variant_id = (
        selection_view.selected_variant_id if selection_view else requested_variant
    )

    preferences_state = compose_preferences(
        selection_view,
        default_variant_ids=config.default_variant_ids,
    )
    preferences_payload = to_payload(preferences_state)

    return render_template(
        "pages/dashboard.html",
        page_title="D3 Item Salvager",
        frontend_config=config,
        variant_summary=variant_summary,
        summary_error=summary_error,
        selection_view=selection_view,
        selection_error=selection_error,
        target_variant_id=target_variant_id,
        preferences_payload=preferences_payload,
    )
