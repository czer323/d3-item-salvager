"""Routes for rendering item usage summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import Blueprint, Response, g, jsonify, render_template, request
from werkzeug.datastructures import ImmutableMultiDict, MultiDict

from frontend.src.services.filtering import parse_page, parse_page_size
from frontend.src.services.item_usage import ItemUsageTable, build_item_usage_table

if TYPE_CHECKING:
    from frontend.src.services.backend_client import BackendClient

items_blueprint = Blueprint("items", __name__, url_prefix="/frontend/items")


def _get_backend_client() -> BackendClient:
    client = getattr(g, "backend_client", None)
    if client is None:
        msg = "Backend client not available in request context"
        raise RuntimeError(msg)
    return cast("BackendClient", client)


SelectionSource = MultiDict[str, str] | ImmutableMultiDict[str, str]


def _build_usage_table(
    client: BackendClient, source: SelectionSource
) -> ItemUsageTable:
    class_ids = source.getlist("class_ids")
    build_ids = source.getlist("build_ids")
    search_term = source.get("search", "")
    slot_filter = source.get("slot") or None
    page = parse_page(source.get("page"), default=1)
    page_size_raw = source.get("page_size")
    page_size = parse_page_size(page_size_raw) if page_size_raw else None

    return build_item_usage_table(
        client,
        class_ids=class_ids,
        build_ids=build_ids,
        search=search_term,
        slot=slot_filter,
        page=page,
        page_size=page_size,
    )


@items_blueprint.route("/summary", methods=["GET", "POST"])
def summary_partial() -> str:
    """Render the item usage table partial."""
    client = _get_backend_client()
    source = request.form if request.method == "POST" else request.args

    table: ItemUsageTable | None = None
    table_error: str | None = None

    try:
        table = _build_usage_table(client, source)
    except Exception as exc:  # pragma: no cover - defensive logging
        table_error = str(exc)

    return render_template(
        "items/summary.html",
        table=table,
        table_error=table_error,
    )


@items_blueprint.route("/summary.json", methods=["GET", "POST"])
def summary_json() -> Response:
    """Return the item usage table as JSON for contract testing."""
    client = _get_backend_client()
    source = request.form if request.method == "POST" else request.args
    try:
        table = _build_usage_table(client, source)
    except Exception as exc:  # pragma: no cover - defensive logging
        error_response = jsonify({"error": str(exc)})
        error_response.status_code = 502
        return error_response
    return jsonify(table.to_contract_payload())
