"""HTMX routes powering the selection controls."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import Blueprint, current_app, g, render_template, request

from frontend.src.services.backend_client import BackendClient, BackendClientError
from frontend.src.services.selection import build_selection_view

if TYPE_CHECKING:
    from frontend.src.config import FrontendConfig

selection_blueprint = Blueprint("selection", __name__, url_prefix="/frontend/selection")


def _get_backend_client() -> BackendClient:
    client = getattr(g, "backend_client", None)
    if client is None:
        msg = "Backend client not available in request context"
        raise RuntimeError(msg)
    return cast("BackendClient", client)


@selection_blueprint.get("/controls")
def controls() -> str:
    """Render the selection controls partial for HTMX swaps."""
    config = cast("FrontendConfig", current_app.config["FRONTEND_CONFIG"])
    client = _get_backend_client()
    class_id = request.args.get("class_id")
    build_id = request.args.get("build_id")
    variant_id = request.args.get("variant") or request.args.get("variant_id")

    selection_error: str | None = None
    selection_view = None

    try:
        selection_view = build_selection_view(
            client,
            default_variant_ids=config.default_variant_ids,
            class_id=class_id,
            build_id=build_id,
            variant_id=variant_id,
        )
    except BackendClientError as exc:
        selection_error = str(exc)
        current_app.logger.exception("Unable to load selection controls")

    return render_template(
        "selection/controls.html",
        selection_view=selection_view,
        selection_error=selection_error,
        prefetch_summary=True,
    )
