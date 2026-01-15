"""HTMX routes powering the selection controls."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import Blueprint, g, render_template, request

from frontend.src.services.backend_client import BackendClient, BackendClientError
from frontend.src.services.selection import build_selection_view

if TYPE_CHECKING:
    from frontend.src.services.selection import SelectionViewModel

selection_blueprint = Blueprint("selection", __name__, url_prefix="/frontend/selection")


def _get_backend_client() -> BackendClient:
    client = getattr(g, "backend_client", None)
    if client is None:
        msg = "Backend client not available in request context"
        raise RuntimeError(msg)
    return cast("BackendClient", client)


@selection_blueprint.route("/controls", methods=["GET", "POST"], endpoint="controls")
def controls_partial() -> str:
    """Render or update the selection controls partial."""
    client = _get_backend_client()

    form = request.form if request.method == "POST" else request.args
    action = form.get("action")
    if action == "reset":
        class_ids: list[str] = []
        build_ids: list[str] = []
        load_builds = False
        prefetch_items = False
    else:
        class_ids = form.getlist("class_ids")
        build_ids = form.getlist("build_ids")
        if action in {"load_builds", "apply_items"}:
            load_builds = True
        else:
            load_builds = bool(build_ids)
        prefetch_items = action == "apply_items"

    selection_view: SelectionViewModel | None = None
    selection_error: str | None = None

    try:
        selection_view = build_selection_view(
            client,
            class_ids=class_ids,
            build_ids=build_ids,
            load_builds=load_builds,
        )
    except BackendClientError as exc:
        selection_error = str(exc)

    # If the user applied the selection, return the panel in collapsed state (summary view)
    if action == "apply_items":
        return render_template(
            "selection_panel.html",
            selection_view=selection_view,
            selection_error=selection_error,
            prefetch_items=prefetch_items,
            selection_collapsed=True,
        )

    return render_template(
        "selection/controls.html",
        selection_view=selection_view,
        selection_error=selection_error,
        prefetch_items=prefetch_items,
    )
