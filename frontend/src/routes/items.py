"""Routes for rendering item usage summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from flask import Blueprint, Response, current_app, g, jsonify, render_template, request
from werkzeug.datastructures import ImmutableMultiDict, MultiDict

from frontend.src.services.backend_client import (
    BackendResponseError,
    BackendTransportError,
)
from frontend.src.services.filtering import parse_page, parse_page_size
from frontend.src.services.item_usage import ItemUsageTable, build_item_usage_table
from frontend.src.services.preferences import PreferencesValidationError

if TYPE_CHECKING:
    from frontend.src.config import FrontendConfig
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
    except (
        PreferencesValidationError,
        ValueError,
    ):  # pragma: no cover - validation errors
        current_app.logger.exception("Validation error while building item usage table")
        table_error = "Invalid request parameters"
    except BackendTransportError:  # pragma: no cover - backend transport / timeout
        current_app.logger.exception(
            "Backend transport error while building item usage table"
        )
        table_error = "Service temporarily unavailable"
    except BackendResponseError:  # pragma: no cover - backend returned non-2xx
        current_app.logger.exception(
            "Backend returned an error while building item usage table"
        )
        table_error = "Upstream service error"
    except RuntimeError as exc:  # pragma: no cover - defensive
        if "Backend client not available" in str(exc):
            current_app.logger.exception(
                "Backend client not available in request context"
            )
            table_error = "Service temporarily unavailable"
        else:
            current_app.logger.exception(
                "Runtime error while building item usage table"
            )
            table_error = "Internal server error"
    except Exception:  # pragma: no cover - defensive logging
        current_app.logger.exception("Unexpected error while building item usage table")
        table_error = "Internal server error"

    # Ensure templates that include shared components receive the frontend config
    # Be defensive: the config key may not be present in some test or runtime setups
    # Retrieve FRONTEND_CONFIG defensively without relying on Mapping.get's overloaded return
    try:
        raw_cfg_any = cast(
            "FrontendConfig | None", current_app.config["FRONTEND_CONFIG"]
        )
    except KeyError:
        raw_cfg_any = None
    config = raw_cfg_any
    if config is None:
        current_app.logger.warning(
            "FRONTEND_CONFIG missing from app config; rendering without it"
        )
    return render_template(
        "items/summary.html",
        table=table,
        table_error=table_error,
        frontend_config=config,
    )


@items_blueprint.route("/summary.json", methods=["GET", "POST"])
def summary_json() -> Response:
    """Return the item usage table as JSON for contract testing."""
    client = _get_backend_client()
    source = request.form if request.method == "POST" else request.args
    try:
        table = _build_usage_table(client, source)
    except (
        PreferencesValidationError,
        ValueError,
    ):  # pragma: no cover - validation errors
        current_app.logger.exception("Validation error building item usage table")
        error_response = jsonify({"error": "Invalid request parameters"})
        error_response.status_code = 400
        return error_response
    except BackendTransportError:  # pragma: no cover - backend transport / timeout
        current_app.logger.exception(
            "Backend transport error building item usage table"
        )
        error_response = jsonify({"error": "Service temporarily unavailable"})
        error_response.status_code = 503
        return error_response
    except BackendResponseError:  # pragma: no cover - backend returned non-2xx
        current_app.logger.exception(
            "Backend returned an error building item usage table"
        )
        error_response = jsonify({"error": "Upstream service error"})
        error_response.status_code = 502
        return error_response
    except RuntimeError as exc:  # pragma: no cover - defensive
        if "Backend client not available" in str(exc):
            current_app.logger.exception(
                "Backend client not available in request context"
            )
            error_response = jsonify({"error": "Service temporarily unavailable"})
            error_response.status_code = 503
            return error_response
        current_app.logger.exception("Runtime error building item usage table")
        error_response = jsonify({"error": "Internal server error"})
        error_response.status_code = 500
        return error_response
    except Exception:  # pragma: no cover - defensive logging
        current_app.logger.exception("Unexpected error building item usage table")
        error_response = jsonify({"error": "Internal server error"})
        error_response.status_code = 500
        return error_response
    return jsonify(table.to_contract_payload())
