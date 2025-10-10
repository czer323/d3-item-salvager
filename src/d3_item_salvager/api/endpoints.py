"""API route definitions for the FastAPI application."""

from fastapi import APIRouter, Query

from d3_item_salvager.api.dependencies import SessionDep
from d3_item_salvager.api.schemas import (
    BuildListResponse,
    BuildSchema,
    ItemListResponse,
    ItemSchema,
    ItemUsageListResponse,
    ItemUsageSchema,
    ProfileListResponse,
    ProfileSchema,
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
