"""Aggregate item catalogue data with usage information for selected builds."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from flask import current_app

from frontend.src.services.backend_catalog import (
    ItemRecord,
    VariantRecord,
    load_item_catalogue,
    load_variants_for_build,
    normalise_id_iterable,
)
from frontend.src.services.backend_catalog import (
    load_builds as fetch_build_records,
)
from frontend.src.services.filtering import (
    FilterCriteria,
    PaginationState,
    apply_filters,
    paginate_items,
)
from frontend.src.services.salvage_classifier import (
    SalvageLabel,
    classify_usage_contexts,
)

if TYPE_CHECKING:
    from frontend.src.services.backend_client import BackendClient


@dataclass(slots=True)
class ItemUsageRow:
    """Representation of a catalogue item with usage metadata."""

    item_id: str
    name: str
    slot: str
    quality: str | None
    is_used: bool
    classification: SalvageLabel
    usage_contexts: tuple[str, ...]
    variant_ids: tuple[str, ...]

    @property
    def badge_class(self) -> str:
        """Return a Tailwind/DaisyUI badge class for this classification."""
        return _BADGE_CLASS_MAP[self.classification]

    @property
    def usage_label(self) -> str:
        """Readable label describing where the item is used."""
        if not self.usage_contexts:
            return ""
        return ", ".join(context.title() for context in self.usage_contexts)


@dataclass(slots=True)
class ItemUsageTable:
    """Aggregated view of item usage and salvage recommendations."""

    rows: list[ItemUsageRow]
    filters: FilterCriteria
    available_slots: tuple[str, ...]
    pagination: PaginationState
    total_items: int
    filtered_items: int
    used_total: int
    filtered_used_total: int
    selected_class_ids: tuple[str, ...]
    selected_build_ids: tuple[str, ...]

    @property
    def has_results(self) -> bool:
        """Return True when any rows are available after filtering."""
        return bool(self.rows)

    def to_contract_payload(self) -> dict[str, Any]:
        """Serialise the table into a JSON-friendly structure."""
        return {
            "filters": {
                "search": self.filters.search,
                "slot": self.filters.slot,
            },
            "available_slots": list(self.available_slots),
            "context": {
                "class_ids": list(self.selected_class_ids),
                "build_ids": list(self.selected_build_ids),
            },
            "totals": {
                "total_items": self.total_items,
                "filtered_items": self.filtered_items,
                "used_total": self.used_total,
                "filtered_used": self.filtered_used_total,
            },
            "rows": [
                {
                    "item_id": row.item_id,
                    "name": row.name,
                    "slot": row.slot,
                    "quality": row.quality,
                    "status": "used",
                    "classification": row.classification.value,
                    "usage_contexts": list(row.usage_contexts),
                    "variant_ids": list(row.variant_ids),
                    "usage_label": row.usage_label,
                }
                for row in self.rows
            ],
        }


def build_item_usage_table(
    client: BackendClient,
    *,
    class_ids: Sequence[str] | None = None,
    build_ids: Sequence[str] | None = None,
    search: str = "",
    slot: str | None = None,
    page: int = 1,
    page_size: int | None = None,
) -> ItemUsageTable:
    """Compose an item usage table for the selected builds."""
    resolved_class_ids = set(normalise_id_iterable(class_ids))
    resolved_build_ids = list(normalise_id_iterable(build_ids))

    if not resolved_build_ids:
        resolved_build_ids = _resolve_builds_for_classes(client, resolved_class_ids)

    catalogue = load_item_catalogue(client)
    usage_map = _collect_usage_for_builds(client, resolved_build_ids)

    rows = _merge_catalogue_with_usage(catalogue, usage_map)
    filters = FilterCriteria(search=search, slot=slot)

    filtered_rows = apply_filters(rows, filters)
    effective_page_size = page_size or max(len(filtered_rows), 1)
    visible_rows, pagination = paginate_items(
        filtered_rows,
        page=page,
        page_size=effective_page_size,
    )

    available_slots = tuple(
        sorted({row.slot for row in rows if row.slot}, key=str.casefold)
    )

    used_total = len(rows)
    filtered_used_total = len(filtered_rows)

    return ItemUsageTable(
        rows=visible_rows,
        filters=filters,
        available_slots=available_slots,
        pagination=pagination,
        total_items=len(rows),
        filtered_items=len(filtered_rows),
        used_total=used_total,
        filtered_used_total=filtered_used_total,
        selected_class_ids=tuple(sorted(resolved_class_ids)),
        selected_build_ids=tuple(resolved_build_ids),
    )


_BADGE_CLASS_MAP: dict[SalvageLabel, str] = {
    SalvageLabel.KEEP: "badge-success",
    SalvageLabel.FOLLOWER: "badge-info",
    SalvageLabel.KANAI: "badge-warning",
    SalvageLabel.SALVAGE: "badge-error",
}


def _resolve_builds_for_classes(
    client: BackendClient,
    class_ids: set[str],
) -> list[str]:
    if not class_ids:
        try:
            return [record.id for record in fetch_build_records(client)]
        except Exception as exc:  # pragma: no cover - defensive logging
            current_app.logger.warning("Unable to resolve builds for classes: %s", exc)
            return []

    try:
        builds = fetch_build_records(client)
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.warning("Unable to load builds: %s", exc)
        return []

    return [record.id for record in builds if record.class_name in class_ids]


def _collect_usage_for_builds(
    client: BackendClient,
    build_ids: Sequence[str],
) -> OrderedDict[str, _UsageAccumulator]:
    usage: OrderedDict[str, _UsageAccumulator] = OrderedDict()
    for build_id in build_ids:
        variants = _safe_load_variants(client, build_id)
        for variant in variants:
            rows = _safe_load_usage_rows(client, variant.id)
            for row in rows:
                item_payload = row.get("item", {})
                if not isinstance(item_payload, Mapping):
                    continue
                item_mapping = cast("Mapping[str, object]", item_payload)
                item_id = str(item_mapping.get("id", "")).strip()
                if not item_id:
                    continue
                name = str(item_mapping.get("name", "Unknown Item"))
                slot = str(item_mapping.get("slot", "Unknown"))
                quality = item_mapping.get("quality")
                quality = str(quality).strip() if quality is not None else None
                context = str(row.get("usage_context", "unknown")).lower()
                accumulator = usage.get(item_id)
                if accumulator is None:
                    accumulator = _UsageAccumulator(
                        name=name,
                        slot=slot,
                        contexts={context},
                        variant_ids={variant.id},
                        quality=quality,
                    )
                    usage[item_id] = accumulator
                else:
                    accumulator.contexts.add(context)
                    accumulator.variant_ids.add(variant.id)
                    # If we didn't have quality yet, prefer the first seen
                    if accumulator.quality is None and quality is not None:
                        accumulator.quality = quality
    return usage


def _merge_catalogue_with_usage(
    catalogue: Sequence[ItemRecord],
    usage: Mapping[str, _UsageAccumulator],
) -> list[ItemUsageRow]:
    rows: list[ItemUsageRow] = []
    catalogue_map = {record.id: record for record in catalogue}

    for item_id, accumulator in usage.items():
        contexts = tuple(sorted(accumulator.contexts))
        classification = classify_usage_contexts(contexts)
        record = catalogue_map.get(item_id)
        name = record.name if record else accumulator.name
        slot = record.slot if record else accumulator.slot
        quality = (
            record.quality
            if record and record.quality is not None
            else getattr(accumulator, "quality", None)
        )
        rows.append(
            ItemUsageRow(
                item_id=item_id,
                name=name,
                slot=slot,
                quality=quality,
                is_used=True,
                classification=classification,
                usage_contexts=contexts,
                variant_ids=tuple(sorted(accumulator.variant_ids)),
            )
        )

    # Sort primarily by item name (case-insensitive) and fall back to item_id
    # to guarantee a deterministic order when names are identical.
    rows.sort(key=lambda row: (row.name.casefold(), row.item_id))
    return rows


def _safe_load_variants(client: BackendClient, build_id: str) -> list[VariantRecord]:
    try:
        return load_variants_for_build(client, build_id)
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.warning("Unable to load variants for %s: %s", build_id, exc)
        return []


def _safe_load_usage_rows(
    client: BackendClient, variant_id: str
) -> list[Mapping[str, object]]:
    try:
        payload = client.get_json(f"/item-usage/{variant_id}")
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.warning(
            "Unable to load item usage for %s: %s", variant_id, exc
        )
        return []

    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, Mapping)]
    return []


@dataclass(slots=True)
class _UsageAccumulator:
    name: str
    slot: str
    contexts: set[str]
    variant_ids: set[str]
    quality: str | None = None


# Public aliases for testability: prefer the public names in tests to avoid
# importing private members (leading underscore) across module boundaries.
# These refer to the same underlying implementations and are intentionally
# exported for use in unit tests.
merge_catalogue_with_usage = _merge_catalogue_with_usage
UsageAccumulator = _UsageAccumulator
