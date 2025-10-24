"""Variant-focused routes for JSON and HTMX responses."""

from __future__ import annotations

from typing import cast

from flask import Blueprint, Response, g, jsonify, render_template, request

from frontend.src.services.backend_client import BackendClient, BackendClientError
from frontend.src.services.variant_summary import (
    VariantDetails,
    VariantSummary,
    build_variant_summary,
)

variants_blueprint = Blueprint("variants", __name__, url_prefix="/frontend/variant")


def _get_backend_client() -> BackendClient:
    client = getattr(g, "backend_client", None)
    if client is None:
        msg = "Backend client not available in request context"
        raise RuntimeError(msg)
    return cast("BackendClient", client)


def _resolve_variant_id(path_variant_id: str) -> str:
    query_variant = request.args.get("variant")
    return query_variant or path_variant_id


@variants_blueprint.get("/<variant_id>.json")
def variant_summary_json(variant_id: str) -> Response:
    """Expose JSON summary for integration and contract tests."""
    client = _get_backend_client()
    summary = _build_summary(client, variant_id)
    return jsonify(summary.to_contract_payload())


@variants_blueprint.get("/<variant_id>")
def variant_summary_partial(variant_id: str) -> str:
    """Render the HTML partial containing used and salvage sections."""
    client = _get_backend_client()
    summary = _build_summary(client, variant_id)
    summary_error = cast("str | None", getattr(g, "summary_error", None))
    return render_template(
        "variants/summary.html",
        summary=summary,
        summary_error=summary_error,
    )


def _build_summary(client: BackendClient, variant_id: str) -> VariantSummary:
    resolved_variant_id = _resolve_variant_id(variant_id)
    try:
        return build_variant_summary(client, resolved_variant_id)
    except BackendClientError as exc:
        fallback = VariantSummary(
            variant=VariantDetails(
                id=resolved_variant_id,
                name=resolved_variant_id,
                build_guide_id="unknown",
            ),
            used_items=[],
            salvage_items=[],
        )
        g.summary_error = str(exc)
        return fallback
