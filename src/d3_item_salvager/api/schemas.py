"""Pydantic response schemas for FastAPI endpoints."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Pagination(BaseModel):
    """Pagination metadata included with list responses."""

    limit: int
    offset: int
    total: int


class ItemSchema(BaseModel):
    """Serializable representation of an item."""

    id: str
    name: str
    type: str
    quality: str

    model_config = ConfigDict(from_attributes=True)


class BuildSchema(BaseModel):
    """Serializable representation of a build guide."""

    id: int
    title: str
    url: str

    model_config = ConfigDict(from_attributes=True)


class BuildGuideSchema(BaseModel):
    """Serializable representation of a build guide with aggregated metadata."""

    id: int
    title: str
    url: str
    class_name: str | None = None


class BuildGuideListResponse(BaseModel):
    """API response payload for build guide listings."""

    data: list[BuildGuideSchema]
    meta: Pagination


class ProfileSchema(BaseModel):
    """Serializable representation of a build profile."""

    id: int
    build_id: int
    name: str
    class_name: str

    model_config = ConfigDict(from_attributes=True)


class VariantSchema(BaseModel):
    """Serializable representation of a build variant for frontend consumers."""

    id: int
    build_guide_id: int
    name: str
    class_name: str


class VariantListResponse(BaseModel):
    """API response payload for variant list endpoints."""

    data: list[VariantSchema]
    meta: Pagination


class ItemUsageSchema(BaseModel):
    """Serializable representation of an item usage entry."""

    id: int
    profile_id: int
    item_id: str
    slot: str
    usage_context: str

    model_config = ConfigDict(from_attributes=True)


class ItemReferenceSchema(BaseModel):
    """Nested item payload exposed in item usage responses."""

    id: str
    name: str
    slot: str


class ItemUsageWithItemSchema(ItemUsageSchema):
    """Item usage entry enriched with nested item metadata."""

    item: ItemReferenceSchema


class ItemListResponse(BaseModel):
    """API response payload for list of items."""

    data: list[ItemSchema]
    meta: Pagination


class BuildListResponse(BaseModel):
    """API response payload for list of builds."""

    data: list[BuildSchema]
    meta: Pagination


class ProfileListResponse(BaseModel):
    """API response payload for list of profiles."""

    data: list[ProfileSchema]
    meta: Pagination


class ItemUsageListResponse(BaseModel):
    """API response payload for list of item usages."""

    data: list[ItemUsageSchema]
    meta: Pagination


def build_pagination(limit: int, offset: int, total: int) -> Pagination:
    """Helper function to build pagination metadata."""
    return Pagination(limit=limit, offset=offset, total=total)
