"""Variant-focused routes for JSON and HTMX responses."""

from __future__ import annotations

from typing import cast

from flask import Blueprint, Response, g, jsonify, render_template, request

from frontend.src.services.backend_client import BackendClient, BackendClientError
from frontend.src.services.filtering import (
    FilterCriteria,
    PaginationState,
    parse_page,
    parse_page_size,
)
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


def _resolve_variant_ids(path_variant_id: str) -> tuple[str, ...]:
    values: list[str] = []
    values.extend(request.args.getlist("variant_ids"))
    values.extend(request.args.getlist("variant"))
    fallback = request.args.get("variant_id")
    if fallback:
        values.append(fallback)
    if not values and path_variant_id:
        values.append(path_variant_id)

    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalised = value.strip()
        if not normalised or normalised in seen:
            continue
        seen.add(normalised)
        unique.append(normalised)
    return tuple(unique)


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
    resolved_variant_ids = _resolve_variant_ids(variant_id)
    search_term = request.args.get("search", "")
    slot_filter = request.args.get("slot")
    used_page = parse_page(request.args.get("used_page"), default=1)
    salvage_page = parse_page(request.args.get("salvage_page"), default=1)
    page_size = parse_page_size(request.args.get("page_size"))
    try:
        return build_variant_summary(
            client,
            resolved_variant_ids,
            search=search_term,
            slot=slot_filter,
            used_page=used_page,
            salvage_page=salvage_page,
            page_size=page_size,
        )
    except BackendClientError as exc:
        filters = FilterCriteria(search=search_term, slot=slot_filter)
        variants = tuple(
            VariantDetails(id=item, name=item, build_guide_id="unknown")
            for item in resolved_variant_ids
        )
        if not variants:
            variants = (
                VariantDetails(
                    id=variant_id,
                    name=variant_id,
                    build_guide_id="unknown",
                ),
            )
        fallback = VariantSummary(
            variants=variants,
            used_items=[],
            salvage_items=[],
            filters=filters,
            available_slots=(),
            used_total=0,
            salvage_total=0,
            filtered_used_total=0,
            filtered_salvage_total=0,
            used_pagination=PaginationState(page=1, page_size=page_size, total_items=0),
            salvage_pagination=PaginationState(
                page=1,
                page_size=page_size,
                total_items=0,
            ),
        )
        g.summary_error = str(exc)
        return fallback
