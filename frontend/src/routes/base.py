"""Base routes for core frontend pages."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import Blueprint, current_app, g, render_template, request

from frontend.src.services.backend_client import BackendClient, BackendClientError
from frontend.src.services.preferences import compose_preferences, to_payload
from frontend.src.services.selection import build_selection_view

if TYPE_CHECKING:
    from frontend.src.config import FrontendConfig

base_blueprint = Blueprint("pages", __name__)


@base_blueprint.get("/")
def dashboard() -> str:
    """Render the dashboard placeholder view."""
    config = cast("FrontendConfig", current_app.config["FRONTEND_CONFIG"])
    selection_view = None
    selection_error: str | None = None

    requested_class_ids = _extract_list_values(
        primary_key="class_ids",
        fallback_keys=("class_id",),
    )
    requested_build_ids = _extract_list_values(
        primary_key="build_ids",
        fallback_keys=("build_id",),
    )
    reset_requested = request.args.get("reset") == "1"
    client = cast("BackendClient | None", getattr(g, "backend_client", None))

    if client is not None:
        try:
            selection_view = build_selection_view(
                client,
                class_ids=() if reset_requested else requested_class_ids,
                build_ids=() if reset_requested else requested_build_ids,
                load_builds=bool(requested_build_ids) and not reset_requested,
            )
        except BackendClientError as exc:
            selection_error = str(exc)
    else:
        selection_error = "Backend client not available"

    preferences_state = compose_preferences(selection_view)
    preferences_payload = to_payload(preferences_state)

    return render_template(
        "pages/dashboard.html",
        page_title="D3 Item Salvager",
        frontend_config=config,
        selection_view=selection_view,
        selection_error=selection_error,
        preferences_payload=preferences_payload,
    )


def _extract_list_values(
    *, primary_key: str, fallback_keys: tuple[str, ...]
) -> list[str]:
    values = list(request.args.getlist(primary_key))
    for key in fallback_keys:
        value = request.args.get(key)
        if value:
            values.append(value)
    return values
