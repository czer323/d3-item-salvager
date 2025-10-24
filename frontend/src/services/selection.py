"""Selection data access helpers for the dashboard controls."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from flask import current_app

from frontend.src.services.backend_client import (
    BackendClient,
    BackendClientError,
    BackendResponseError,
)

JSONDict = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ClassOption:
    """Selectable representation of a character class."""

    id: str
    label: str
    build_count: int
    selected: bool


@dataclass(frozen=True, slots=True)
class BuildOption:
    """Selectable representation of a build guide."""

    id: str
    label: str
    class_id: str
    selected: bool


@dataclass(frozen=True, slots=True)
class VariantOption:
    """Selectable representation of a build variant."""

    id: str
    label: str
    build_id: str
    selected: bool


@dataclass(frozen=True, slots=True)
class SelectionViewModel:
    """Aggregated options used to render the selection controls."""

    classes: tuple[ClassOption, ...]
    builds: tuple[BuildOption, ...]
    variants: tuple[VariantOption, ...]
    selected_class_id: str | None
    selected_build_id: str | None
    selected_variant_id: str | None

    @property
    def has_variants(self) -> bool:
        """Return True when variant options are available."""
        return bool(self.variants)


@dataclass(frozen=True, slots=True)
class _BuildRecord:
    """Internal representation of build metadata."""

    id: str
    title: str
    class_name: str


def build_selection_view(
    client: BackendClient,
    *,
    default_variant_ids: Sequence[str] = (),
    class_id: str | None = None,
    build_id: str | None = None,
    variant_id: str | None = None,
) -> SelectionViewModel:
    """Compose selection controls for the dashboard views."""
    builds = _load_builds(client)
    normalized_variant_id = _normalize_id(variant_id) or _first(default_variant_ids)
    normalized_build_id = _normalize_id(build_id)
    normalized_class_id = _normalize_id(class_id)

    if not builds:
        return SelectionViewModel(
            classes=(),
            builds=(),
            variants=(),
            selected_class_id=normalized_class_id,
            selected_build_id=normalized_build_id,
            selected_variant_id=normalized_variant_id,
        )

    build_map = {record.id: record for record in builds}

    if normalized_variant_id and normalized_build_id is None:
        variant_details = _fetch_variant_details(client, normalized_variant_id)
        candidate_build = _normalize_id(
            variant_details.get("build_guide_id") if variant_details else None
        )
        if candidate_build:
            normalized_build_id = candidate_build

    class_groups: dict[str, list[_BuildRecord]] = defaultdict(list)
    for record in builds:
        class_groups[record.class_name].append(record)

    sorted_classes = sorted(class_groups.keys(), key=str.casefold)

    if normalized_class_id not in class_groups:
        if normalized_build_id and normalized_build_id in build_map:
            normalized_class_id = build_map[normalized_build_id].class_name
        elif sorted_classes:
            normalized_class_id = sorted_classes[0]

    if normalized_class_id is None:
        active_class_builds: tuple[_BuildRecord, ...] = ()
    else:
        selected_builds = class_groups.get(normalized_class_id)
        if selected_builds is None:
            active_class_builds = ()
        else:
            active_class_builds = tuple(
                sorted(
                    selected_builds,
                    key=lambda record: record.title.casefold(),
                )
            )

    if normalized_build_id not in {record.id for record in active_class_builds}:
        normalized_build_id = _first([record.id for record in active_class_builds])

    class_options = tuple(
        ClassOption(
            id=class_name,
            label=class_name,
            build_count=len(class_groups[class_name]),
            selected=class_name == normalized_class_id,
        )
        for class_name in sorted_classes
    )

    build_options = tuple(
        BuildOption(
            id=record.id,
            label=record.title,
            class_id=record.class_name,
            selected=record.id == normalized_build_id,
        )
        for record in active_class_builds
    )

    variants_payload: list[JSONDict] = []
    if normalized_build_id:
        try:
            variants_payload = _fetch_variants_for_build(client, normalized_build_id)
        except BackendClientError as exc:
            current_app.logger.warning(
                "Unable to load variants for build %s: %s",
                normalized_build_id,
                exc,
            )
            variants_payload = []

    variant_options = _build_variant_options(
        variants_payload,
        selected_build_id=normalized_build_id,
        requested_variant_id=normalized_variant_id,
    )
    updated_variant_id = _resolve_variant_selection(
        variant_options, normalized_variant_id
    )

    return SelectionViewModel(
        classes=class_options,
        builds=build_options,
        variants=variant_options,
        selected_class_id=normalized_class_id,
        selected_build_id=normalized_build_id,
        selected_variant_id=updated_variant_id,
    )


def _build_variant_options(
    payload: list[JSONDict],
    *,
    selected_build_id: str | None,
    requested_variant_id: str | None,
) -> tuple[VariantOption, ...]:
    options: list[VariantOption] = []
    for row in payload:
        variant_id = _normalize_id(row.get("id"))
        if not variant_id:
            continue
        label_raw = row.get("name") or variant_id
        label = str(label_raw).strip() or variant_id
        option = VariantOption(
            id=variant_id,
            label=label,
            build_id=selected_build_id or "",
            selected=False,
        )
        options.append(option)

    options.sort(key=lambda option: option.label.casefold())

    requested = requested_variant_id or (options[0].id if options else None)
    resolved = (
        VariantOption(
            id=option.id,
            label=option.label,
            build_id=option.build_id,
            selected=option.id == requested,
        )
        for option in options
    )
    return tuple(resolved)


def _resolve_variant_selection(
    variants: tuple[VariantOption, ...],
    requested_variant_id: str | None,
) -> str | None:
    if not variants:
        return requested_variant_id
    for option in variants:
        if option.selected:
            return option.id
    return variants[0].id


def _fetch_variant_details(client: BackendClient, variant_id: str) -> JSONDict:
    candidate_paths = (
        f"/variants/{variant_id}",
        f"/profiles/{variant_id}",
    )
    for path in candidate_paths:
        try:
            payload = client.get_json(path)
        except BackendClientError:
            continue
        details = _collect_dict(payload)
        if details:
            return details
    return {}


def _fetch_variants_for_build(client: BackendClient, build_id: str) -> list[JSONDict]:
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
        variants = _collect_dict_list(payload)
        if variants:
            return variants
    return []


def _load_builds(client: BackendClient) -> list[_BuildRecord]:
    candidate_paths = ("/build-guides", "/builds")
    for path in candidate_paths:
        try:
            payload = client.get_json(path)
        except BackendClientError:
            continue
        rows = _collect_dict_list(payload)
        if not rows:
            continue
        records: list[_BuildRecord] = []
        for row in rows:
            build_id = _normalize_id(row.get("id"))
            if build_id is None:
                continue
            title_raw = row.get("title") or row.get("name") or build_id
            title = str(title_raw).strip() or build_id
            class_name_raw = row.get("class_name") or row.get("class") or "Unknown"
            class_name = str(class_name_raw).strip() or "Unknown"
            records.append(
                _BuildRecord(id=build_id, title=title, class_name=class_name)
            )
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


def _collect_dict_list(payload: object) -> list[JSONDict]:
    """Convert a payload into a list of JSON dictionaries with string keys."""
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


def _collect_dict(payload: object) -> JSONDict | None:
    """Convert a payload into a JSON dictionary with string keys when possible."""
    if isinstance(payload, Mapping):
        mapping_payload = cast("Mapping[object, object]", payload)
        data_value = mapping_payload.get("data")
        if isinstance(data_value, Mapping):
            data_mapping = cast("Mapping[object, object]", data_value)
            return {str(key): value for key, value in data_mapping.items()}
        return {str(key): value for key, value in mapping_payload.items()}
    return None


def _normalize_id(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first(values: Sequence[str] | Sequence[object]) -> str | None:
    for value in values:
        normalized = _normalize_id(value)
        if normalized:
            return normalized
    return None
