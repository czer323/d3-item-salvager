"""Aggregate item catalogue data with usage information for selected builds."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
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


class ItemUsageStatus(str, Enum):
    """Disposition of an item relative to the selected builds."""

    USED = "used"
    SALVAGE = "salvage"


@dataclass(slots=True)
class ItemUsageRow:
    """Representation of a catalogue item with usage metadata."""

    item_id: str
    name: str
    slot: str
    status: ItemUsageStatus
    classification: SalvageLabel
    usage_contexts: tuple[str, ...]
    variant_ids: tuple[str, ...]

    @property
    def badge_class(self) -> str:
        """Return a Tailwind/DaisyUI badge class for this classification."""
        return _BADGE_CLASS_MAP[self.classification]

    @property
    def is_used(self) -> bool:
        """Return True when the item is required for the selected builds."""
        return self.status is ItemUsageStatus.USED

    @property
    def usage_label(self) -> str:
        """Readable label describing where the item is used."""
        if not self.usage_contexts:
            return "Salvage"
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
    salvage_total: int
    filtered_used_total: int
    filtered_salvage_total: int
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
                "salvage_total": self.salvage_total,
                "filtered_salvage": self.filtered_salvage_total,
            },
            "rows": [
                {
                    "item_id": row.item_id,
                    "name": row.name,
                    "slot": row.slot,
                    "status": row.status.value,
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

    used_total = sum(1 for row in rows if row.status is ItemUsageStatus.USED)
    salvage_total = len(rows) - used_total
    filtered_used_total = sum(
        1 for row in filtered_rows if row.status is ItemUsageStatus.USED
    )
    filtered_salvage_total = len(filtered_rows) - filtered_used_total

    return ItemUsageTable(
        rows=visible_rows,
        filters=filters,
        available_slots=available_slots,
        pagination=pagination,
        total_items=len(rows),
        filtered_items=len(filtered_rows),
        used_total=used_total,
        salvage_total=salvage_total,
        filtered_used_total=filtered_used_total,
        filtered_salvage_total=filtered_salvage_total,
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
                context = str(row.get("usage_context", "unknown")).lower()
                accumulator = usage.get(item_id)
                if accumulator is None:
                    accumulator = _UsageAccumulator(
                        name=name,
                        slot=slot,
                        contexts={context},
                        variant_ids={variant.id},
                    )
                    usage[item_id] = accumulator
                else:
                    accumulator.contexts.add(context)
                    accumulator.variant_ids.add(variant.id)
    return usage


def _merge_catalogue_with_usage(
    catalogue: Sequence[ItemRecord],
    usage: Mapping[str, _UsageAccumulator],
) -> list[ItemUsageRow]:
    rows: list[ItemUsageRow] = []
    catalogue_map = {record.id: record for record in catalogue}

    for record in catalogue:
        accumulator = usage.get(record.id)
        if accumulator:
            contexts = tuple(sorted(accumulator.contexts))
            classification = classify_usage_contexts(contexts)
            rows.append(
                ItemUsageRow(
                    item_id=record.id,
                    name=record.name,
                    slot=record.slot,
                    status=ItemUsageStatus.USED,
                    classification=classification,
                    usage_contexts=contexts,
                    variant_ids=tuple(sorted(accumulator.variant_ids)),
                )
            )
        else:
            rows.append(
                ItemUsageRow(
                    item_id=record.id,
                    name=record.name,
                    slot=record.slot,
                    status=ItemUsageStatus.SALVAGE,
                    classification=SalvageLabel.SALVAGE,
                    usage_contexts=(),
                    variant_ids=(),
                )
            )

    # Include any usage entries not present in the catalogue for completeness.
    for item_id, accumulator in usage.items():
        if item_id in catalogue_map:
            continue
        contexts = tuple(sorted(accumulator.contexts))
        classification = classify_usage_contexts(contexts)
        rows.append(
            ItemUsageRow(
                item_id=item_id,
                name=accumulator.name,
                slot=accumulator.slot,
                status=ItemUsageStatus.USED,
                classification=classification,
                usage_contexts=contexts,
                variant_ids=tuple(sorted(accumulator.variant_ids)),
            )
        )

    rows.sort(
        key=lambda row: (row.status.value, row.slot.casefold(), row.name.casefold())
    )
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
