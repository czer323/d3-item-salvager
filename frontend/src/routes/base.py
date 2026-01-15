"""Base routes for core frontend pages."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from flask import Blueprint, current_app, g, render_template, request

from frontend.src.config import FrontendConfig
from frontend.src.services.backend_client import BackendClient, BackendClientError
from frontend.src.services.preferences import compose_preferences, to_payload
from frontend.src.services.selection import build_selection_view

base_blueprint = Blueprint("pages", __name__)


FrontendConfigLike = FrontendConfig | SimpleNamespace


def _load_frontend_config() -> FrontendConfigLike | None:
    if "FRONTEND_CONFIG" not in current_app.config:
        return None
    return cast("FrontendConfigLike", current_app.config["FRONTEND_CONFIG"])


@base_blueprint.get("/")
def dashboard() -> str:
    """Render the dashboard placeholder view."""
    # Be defensive in case FRONTEND_CONFIG is missing (tests or runtime)
    config = _load_frontend_config()
    if config is None:
        current_app.logger.warning(
            "FRONTEND_CONFIG missing from app config; rendering without it"
        )
    selection_view = None
    selection_error: str | None = None

    requested_class_ids = extract_list_values(
        primary_key="class_ids",
        fallback_keys=("class_id",),
    )
    requested_build_ids = extract_list_values(
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

    # Collapse selection summary only when the request explicitly included build_ids
    selection_collapsed = bool(requested_build_ids)

    return render_template(
        "pages/dashboard.html",
        page_title="D3 Item Salvager",
        frontend_config=config,
        selection_view=selection_view,
        selection_error=selection_error,
        preferences_payload=preferences_payload,
        selection_collapsed=selection_collapsed,
    )


def extract_list_values(
    *, primary_key: str, fallback_keys: tuple[str, ...]
) -> list[str]:
    values = list(request.args.getlist(primary_key))
    for key in fallback_keys:
        value = request.args.get(key)
        if value:
            values.append(value)

    # Deduplicate while preserving order so callers receive unique values
    seen: set[str] = set()
    unique_values: list[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            unique_values.append(v)

    return unique_values
