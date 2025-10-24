"""API route definitions for the FastAPI application."""

from fastapi import APIRouter, HTTPException, Query

from d3_item_salvager.api.dependencies import SessionDep
from d3_item_salvager.api.schemas import (
    BuildGuideListResponse,
    BuildGuideSchema,
    BuildListResponse,
    BuildSchema,
    ItemListResponse,
    ItemReferenceSchema,
    ItemSchema,
    ItemUsageListResponse,
    ItemUsageSchema,
    ItemUsageWithItemSchema,
    ProfileListResponse,
    ProfileSchema,
    VariantListResponse,
    VariantSchema,
    build_pagination,
)
from d3_item_salvager.data import queries

router = APIRouter()

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500


@router.get("/items", response_model=ItemListResponse, tags=["items"])
async def list_items(
    session: SessionDep,
    *,
    class_name: str | None = Query(None, description="Filter items by character class"),
    slot: str | None = Query(None, description="Filter items by equipment slot"),
    set_status: str | None = Query(
        None, description="Filter items by set or legendary status"
    ),
    usage_context: str | None = Query(
        None, description="Filter items by usage context (main, follower, kanai)"
    ),
    limit: int = Query(
        _DEFAULT_LIMIT,
        ge=1,
        le=_MAX_LIMIT,
        description="Maximum number of records to return",
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> ItemListResponse:
    """Return a filtered list of items."""
    items, total = queries.list_items(
        session,
        class_name=class_name,
        slot=slot,
        set_status=set_status,
        usage_context=usage_context,
        limit=limit,
        offset=offset,
    )
    payload = [ItemSchema.model_validate(item) for item in items]
    return ItemListResponse(data=payload, meta=build_pagination(limit, offset, total))


@router.get("/builds", response_model=BuildListResponse, tags=["builds"])
async def list_builds(
    session: SessionDep,
    *,
    limit: int = Query(
        _DEFAULT_LIMIT,
        ge=1,
        le=_MAX_LIMIT,
        description="Maximum number of records to return",
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> BuildListResponse:
    """Return a paginated list of build guides."""
    builds, total = queries.list_builds(session, limit=limit, offset=offset)
    payload = [BuildSchema.model_validate(build) for build in builds]
    return BuildListResponse(data=payload, meta=build_pagination(limit, offset, total))


@router.get("/profiles", response_model=ProfileListResponse, tags=["profiles"])
async def list_profiles(
    session: SessionDep,
    *,
    class_name: str | None = Query(None, description="Filter profiles by class name"),
    build_id: int | None = Query(None, ge=1, description="Filter profiles by build id"),
    limit: int = Query(
        _DEFAULT_LIMIT,
        ge=1,
        le=_MAX_LIMIT,
        description="Maximum number of records to return",
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> ProfileListResponse:
    """Return a filtered list of build profiles."""
    profiles, total = queries.list_profiles(
        session,
        class_name=class_name,
        build_id=build_id,
        limit=limit,
        offset=offset,
    )
    payload = [ProfileSchema.model_validate(profile) for profile in profiles]
    return ProfileListResponse(
        data=payload, meta=build_pagination(limit, offset, total)
    )


@router.get("/item_usages", response_model=ItemUsageListResponse, tags=["item_usages"])
async def list_item_usages(
    session: SessionDep,
    *,
    profile_id: int | None = Query(
        None, ge=1, description="Filter by profile identifier"
    ),
    item_id: str | None = Query(None, description="Filter by item identifier"),
    usage_context: str | None = Query(
        None, description="Filter by usage context (main, follower, kanai)"
    ),
    limit: int = Query(
        _DEFAULT_LIMIT,
        ge=1,
        le=_MAX_LIMIT,
        description="Maximum number of records to return",
    ),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> ItemUsageListResponse:
    """Return a filtered list of item usages."""
    usages, total = queries.list_item_usages(
        session,
        profile_id=profile_id,
        item_id=item_id,
        usage_context=usage_context,
        limit=limit,
        offset=offset,
    )
    payload = [ItemUsageSchema.model_validate(usage) for usage in usages]
    return ItemUsageListResponse(
        data=payload, meta=build_pagination(limit, offset, total)
    )


@router.get(
    "/build-guides", response_model=BuildGuideListResponse, tags=["build-guides"]
)
async def list_build_guides(session: SessionDep) -> BuildGuideListResponse:
    """Return build guides enriched with inferred class metadata."""
    rows = queries.list_build_guides_with_classes(session)
    data: list[BuildGuideSchema] = []
    for build, class_name in rows:
        if build.id is None:
            continue
        data.append(
            BuildGuideSchema(
                id=build.id,
                title=build.title,
                url=build.url,
                class_name=class_name or "Unknown",
            )
        )
    return BuildGuideListResponse(data=data)


@router.get(
    "/build-guides/{build_id}/variants",
    response_model=VariantListResponse,
    tags=["variants"],
)
async def list_variants(
    build_id: int,
    session: SessionDep,
) -> VariantListResponse:
    """Return variants (profiles) associated with a build guide."""
    profiles = queries.list_variants_for_build(session, build_id)
    payload: list[VariantSchema] = []
    for profile in profiles:
        if profile.id is None:
            continue
        payload.append(
            VariantSchema(
                id=profile.id,
                name=profile.name,
                build_guide_id=profile.build_id,
                class_name=profile.class_name,
            )
        )
    return VariantListResponse(data=payload)


@router.get(
    "/variants/{variant_id}",
    response_model=VariantSchema,
    tags=["variants"],
)
async def get_variant(variant_id: int, session: SessionDep) -> VariantSchema:
    """Return details for a single variant (profile)."""
    profile = queries.get_variant(session, variant_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Variant not found")
    if profile.id is None:
        raise HTTPException(status_code=404, detail="Variant not found")
    return VariantSchema(
        id=profile.id,
        name=profile.name,
        build_guide_id=profile.build_id,
        class_name=profile.class_name,
    )


@router.get(
    "/item-usage/{variant_id}",
    response_model=list[ItemUsageWithItemSchema],
    tags=["item-usage"],
)
async def list_item_usage_for_variant(
    variant_id: int,
    session: SessionDep,
) -> list[ItemUsageWithItemSchema]:
    """Return item usage entries (with nested item metadata) for a variant."""
    rows = queries.list_item_usage_with_items(session, variant_id)
    payload: list[ItemUsageWithItemSchema] = []
    for usage, item in rows:
        if usage.id is None:
            continue
        payload.append(
            ItemUsageWithItemSchema(
                id=usage.id,
                profile_id=usage.profile_id,
                item_id=usage.item_id,
                slot=usage.slot,
                usage_context=usage.usage_context,
                item=ItemReferenceSchema(
                    id=item.id,
                    name=item.name,
                    slot=item.type or usage.slot,
                ),
            )
        )
    return payload
