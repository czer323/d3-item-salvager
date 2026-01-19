"""Web routes for the HTML frontend."""

import json
from collections import defaultdict
from typing import Annotated, Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from d3_item_salvager.api.dependencies import SessionDep
from d3_item_salvager.api.templating import templates
from d3_item_salvager.data import queries
from d3_item_salvager.services.ui import UIService

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, session: SessionDep) -> HTMLResponse:
    """Render the main dashboard."""
    rows = queries.list_build_guides_with_classes(session)

    # Group builds by class for the UI selector
    builds_by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for build, class_name in rows:
        if not class_name or not build.id:
            continue
        builds_by_class[class_name].append(
            {"id": build.id, "title": build.title, "url": build.url}
        )

    # Sort classes and builds
    sorted_classes = sorted(builds_by_class.keys())
    for cls in sorted_classes:
        builds_by_class[cls].sort(key=lambda b: b["title"])

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "builds_by_class": builds_by_class,
            "sorted_classes": sorted_classes,
        },
    )


@router.post("/hx/items", response_class=HTMLResponse)
async def get_items(
    request: Request,
    session: SessionDep,
    build_ids: Annotated[list[str], Form()] = [],
) -> HTMLResponse:
    """Return the salvage table for selected builds."""
    variant_ids: list[int] = []

    for build_id_str in build_ids:
        try:
            bid = int(build_id_str)
            variants = queries.list_variants_for_build(session, bid)
            variant_ids.extend(v.id for v in variants if v.id is not None)
        except ValueError:
            continue

    # 2. Get Items via Service
    service = UIService(session)
    items = service.get_salvage_table(variant_ids)

    # 3. Serialize for Alpine
    items_data = [item.model_dump() for item in items]

    return templates.TemplateResponse(
        request=request,
        name="partials/items_table.html",
        context={"items_json": json.dumps(items_data)},
    )
