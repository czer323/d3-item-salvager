"""Shared helpers for loading build, variant, and item data from the backend."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from frontend.src.services.backend_client import (
    BackendClient,
    BackendClientError,
    BackendResponseError,
)

JSONDict = dict[str, Any]


@dataclass(frozen=True, slots=True)
class BuildRecord:
    """Normalized representation of a build guide returned by the backend."""

    id: str
    title: str
    class_name: str


@dataclass(frozen=True, slots=True)
class VariantRecord:
    """Normalized representation of a variant entry returned by the backend."""

    id: str
    name: str
    build_id: str


@dataclass(frozen=True, slots=True)
class ItemRecord:
    """Normalized representation of an item in the catalogue."""

    id: str
    name: str
    slot: str
    quality: str | None = None


def normalize_class_name(raw: object | None) -> str:
    """Normalize class names returned by the backend to the canonical display form.

    Mirrors server-side normalization: removes non-alphanumeric characters for keying
    and maps known compact variants to Title Case labels. Falls back to title-casing.
    """
    if raw is None:
        return "Unknown"
    s = str(raw).strip()
    key = "".join(ch for ch in s.lower() if ch.isalnum())
    mapping: dict[str, str] = {
        "barbarian": "Barbarian",
        "crusader": "Crusader",
        "demonhunter": "Demon Hunter",
        "monk": "Monk",
        "necromancer": "Necromancer",
        "witchdoctor": "Witch Doctor",
        "wizard": "Wizard",
        "druid": "Druid",
    }
    return mapping.get(key, s.title() if s else "Unknown")


def load_builds(client: BackendClient) -> list[BuildRecord]:
    """Load all build guides from the backend service."""
    candidate_paths = ("/build-guides", "/builds")
    for path in candidate_paths:
        try:
            payload = client.get_json(path)
        except BackendClientError:
            continue
        rows = collect_dict_list(payload)
        if not rows:
            continue
        records: list[BuildRecord] = []
        for row in rows:
            build_id = normalize_id(row.get("id"))
            if build_id is None:
                continue
            title_raw = row.get("title") or row.get("name") or build_id
            title = str(title_raw).strip() or build_id
            class_name_raw = row.get("class_name") or row.get("class") or "Unknown"
            class_name = normalize_class_name(class_name_raw)
            records.append(BuildRecord(id=build_id, title=title, class_name=class_name))
        if records:
            records.sort(
                key=lambda record: (
                    record.class_name.casefold(),
                    record.title.casefold(),
                )
            )
            return records
    msg = "Backend returned no build guides"
    raise BackendResponseError(msg)


def load_variants_for_build(
    client: BackendClient, build_id: str
) -> list[VariantRecord]:
    """Load all variants for a given build, trying known endpoint patterns."""
    candidate_paths = (
        f"/build-guides/{build_id}/variants",
        f"/builds/{build_id}/variants",
        f"/variants/{build_id}",
    )
    for path in candidate_paths:
        try:
            payload = client.get_json(path)
        except BackendClientError:
            continue
        rows = collect_dict_list(payload)
        if not rows:
            continue
        records: list[VariantRecord] = []
        for row in rows:
            variant_id = normalize_id(row.get("id"))
            if variant_id is None:
                continue
            name_raw = row.get("name") or variant_id
            name = str(name_raw).strip() or variant_id
            records.append(VariantRecord(id=variant_id, name=name, build_id=build_id))
        if records:
            records.sort(key=lambda record: record.name.casefold())
            return records
    return []


def load_item_catalogue(client: BackendClient) -> list[ItemRecord]:
    """Load the full item catalogue from the backend."""
    candidate_paths = ("/items", "/item-catalogue", "/item-catalog")
    for path in candidate_paths:
        try:
            payload = client.get_json(path)
        except BackendClientError:
            continue
        rows = collect_dict_list(payload)
        if not rows:
            continue
        records: list[ItemRecord] = []
        for row in rows:
            item_id = normalize_id(row.get("id"))
            if item_id is None:
                continue
            name_raw = row.get("name") or item_id
            name = str(name_raw).strip() or item_id
            slot_raw = row.get("slot") or "Unknown"
            slot = str(slot_raw).strip() or "Unknown"
            quality_raw = row.get("quality")
            quality = str(quality_raw).strip() if quality_raw is not None else None
            records.append(
                ItemRecord(id=item_id, name=name, slot=slot, quality=quality)
            )
        if records:
            records.sort(key=lambda record: record.name.casefold())
            return records
    msg = "Backend returned no item catalogue"
    raise BackendResponseError(msg)


def collect_dict_list(payload: object) -> list[JSONDict]:
    """Convert payloads into a list of dictionaries."""
    if isinstance(payload, Sequence) and not isinstance(
        payload, (str, bytes, bytearray)
    ):
        source_iterable: Sequence[object] = cast("Sequence[object]", payload)
    elif isinstance(payload, Mapping):
        mapping_payload = cast("Mapping[object, object]", payload)
        data_value = mapping_payload.get("data")
        if isinstance(data_value, Sequence) and not isinstance(
            data_value, (str, bytes, bytearray)
        ):
            source_iterable = cast("Sequence[object]", data_value)
        else:
            return []
    else:
        return []

    result: list[JSONDict] = []
    for item in source_iterable:
        if isinstance(item, Mapping):
            mapping_item = cast("Mapping[object, object]", item)
            typed_item: JSONDict = {
                str(key): value for key, value in mapping_item.items()
            }
            result.append(typed_item)
    return result


def normalize_id(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalise_id_iterable(
    values: Sequence[str] | Iterable[object] | None,
) -> tuple[str, ...]:
    if values is None:
        return ()
    normalised: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalised_value = normalize_id(value)
        if not normalised_value:
            continue
        if normalised_value in seen:
            continue
        seen.add(normalised_value)
        normalised.append(normalised_value)
    return tuple(normalised)
