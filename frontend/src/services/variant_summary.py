"""Aggregate backend responses into variant summary objects."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from typing import Any, cast

from flask import current_app

from frontend.src.services.backend_client import (
    BackendClient,
    BackendClientError,
    BackendResponseError,
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


@dataclass(slots=True)
class VariantDetails:
    """Metadata describing a selected variant."""

    id: str
    name: str
    build_guide_id: str


@dataclass(slots=True)
class ItemSummary:
    """Representation of a deduplicated item and its usage contexts."""

    item_id: str
    name: str
    slot: str
    usage_contexts: tuple[str, ...]
    classification: SalvageLabel
    variant_ids: tuple[str, ...]

    @property
    def usage_label(self) -> str:
        """Readable usage label summarising contexts."""
        return ", ".join(context.title() for context in self.usage_contexts)

    @property
    def badge_class(self) -> str:
        """Return a Tailwind/DaisyUI badge class for this classification."""
        return _BADGE_MAP[self.classification]

    @property
    def variant_count(self) -> int:
        """Return the number of variants that use this item."""
        return len(self.variant_ids)

    def to_contract_entry(self) -> dict[str, Any]:
        """Convert into the contract-compliant JSON payload."""
        primary_context = self.usage_contexts[0] if self.usage_contexts else "unknown"
        return {
            "item_id": self.item_id,
            "usage_context": primary_context,
            "usage_contexts": list(self.usage_contexts),
            "item": {"id": self.item_id, "name": self.name, "slot": self.slot},
            "classification": self.classification.value,
        }


@dataclass(slots=True)
class VariantSummary:
    """Aggregate of used items for a variant."""

    variants: tuple[VariantDetails, ...]
    used_items: list[ItemSummary]
    all_items: list[ItemSummary]
    filters: FilterCriteria
    available_slots: tuple[str, ...]
    used_total: int
    filtered_used_total: int
    used_pagination: PaginationState

    def to_contract_payload(self) -> dict[str, Any]:
        """Return JSON payload adhering to the documented contract."""
        variant_payload = (
            asdict(self.variants[0])
            if self.variants
            else {"id": "unknown", "name": "Combined", "build_guide_id": "unknown"}
        )
        return {
            "variant": variant_payload,
            "items": [item.to_contract_entry() for item in self.all_items],
        }

    @property
    def variant_count(self) -> int:
        """Return how many variants contribute to this summary."""
        return len(self.variants)

    @property
    def variant_names(self) -> tuple[str, ...]:
        """Return variant names in the order they were processed."""
        return tuple(variant.name for variant in self.variants)


def build_variant_summary(
    client: BackendClient,
    variant_ids: Sequence[str] | str,
    *,
    search: str = "",
    slot: str | None = None,
    used_page: int = 1,
    page_size: int = 60,
) -> VariantSummary:
    """Fetch backend data and compose a variant summary."""
    processed_variant_ids = _normalise_ids(variant_ids)
    if not processed_variant_ids:
        msg = "At least one variant identifier is required"
        raise BackendResponseError(msg)

    variants: list[VariantDetails] = [
        _fetch_variant_details(client, variant_id)
        for variant_id in processed_variant_ids
    ]

    usage_rows_by_variant: dict[str, list[dict[str, Any]]] = {}
    for variant_id in processed_variant_ids:
        usage_rows = client.get_json(f"/item-usage/{variant_id}")
        if isinstance(usage_rows, list):
            usage_rows_by_variant[variant_id] = [
                row for row in usage_rows if isinstance(row, dict)
            ]
        else:
            msg = "Expected backend to return a list of usage rows"
            raise BackendResponseError(msg)

    deduped: OrderedDict[str, _ItemAccumulator] = OrderedDict()

    for variant_id, usage_rows in usage_rows_by_variant.items():
        for row in usage_rows:
            item_payload = row.get("item", {})
            if not isinstance(item_payload, dict):
                current_app.logger.debug(
                    "Skipping usage row without item payload: %s", row
                )
                continue
            item_mapping = cast("dict[str, Any]", item_payload)
            item_id = str(item_mapping.get("id", ""))
            if not item_id:
                current_app.logger.debug(
                    "Skipping malformed usage row with missing id: %s", row
                )
                continue
            name = str(item_mapping.get("name", "Unknown Item"))
            slot = str(item_mapping.get("slot", "Unknown"))
            context = str(row.get("usage_context", "unknown")).lower()

            accumulator = deduped.get(item_id)
            if accumulator is None:
                accumulator = _ItemAccumulator(
                    name=name,
                    slot=slot,
                    contexts={context},
                    variant_ids={variant_id},
                )
                deduped[item_id] = accumulator
            else:
                accumulator.contexts.add(context)
                accumulator.variant_ids.add(variant_id)

    used_items: list[ItemSummary] = []
    all_items: list[ItemSummary] = []
    for item_id, accumulator in deduped.items():
        contexts = tuple(sorted(accumulator.contexts))
        classification = classify_usage_contexts(contexts)
        summary = ItemSummary(
            item_id=item_id,
            name=accumulator.name,
            slot=accumulator.slot,
            usage_contexts=contexts,
            classification=classification,
            variant_ids=tuple(sorted(accumulator.variant_ids)),
        )
        all_items.append(summary)
        # Exclude 'salvage' classification from the visible lists
        if classification is not SalvageLabel.SALVAGE:
            used_items.append(summary)

    available_slots = tuple(
        sorted({item.slot for item in used_items if item.slot}, key=str.casefold)
    )
    criteria = FilterCriteria(search=search, slot=slot)
    filtered_used = apply_filters(used_items, criteria)
    used_page_items, used_pagination = paginate_items(
        filtered_used,
        page=used_page,
        page_size=page_size,
    )

    current_app.logger.warning(
        "build_variant_summary: used_items=%d, deduped=%d, variants=%s",
        len(used_items),
        len(deduped),
        list(usage_rows_by_variant.keys()),
    )

    return VariantSummary(
        variants=tuple(variants),
        used_items=used_page_items,
        all_items=all_items,
        filters=criteria,
        available_slots=available_slots,
        used_total=len(used_items),
        filtered_used_total=len(filtered_used),
        used_pagination=used_pagination,
    )


_BADGE_MAP: dict[SalvageLabel, str] = {
    SalvageLabel.KEEP: "badge-success",
    SalvageLabel.FOLLOWER: "badge-info",
    SalvageLabel.KANAI: "badge-warning",
    SalvageLabel.SALVAGE: "badge-error",
}


def _fetch_variant_details(client: BackendClient, variant_id: str) -> VariantDetails:
    """Retrieve metadata for a variant, applying sensible fallbacks."""
    try:
        payload = client.get_json(f"/variants/{variant_id}")
    except BackendClientError:
        payload = None

    if isinstance(payload, dict):
        variant_id = str(payload.get("id", variant_id))
        name = str(payload.get("name", variant_id))
        build_guide_id = str(payload.get("build_guide_id", "unknown"))
        return VariantDetails(id=variant_id, name=name, build_guide_id=build_guide_id)

    return VariantDetails(id=variant_id, name=variant_id, build_guide_id="unknown")


def _normalise_ids(values: Sequence[str] | str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, str):
        iterable: Iterable[str] = (values,)
    elif isinstance(values, Sequence):
        iterable = values
    else:
        iterable = tuple(values)

    normalised: list[str] = []
    seen: set[str] = set()
    for value in iterable:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalised.append(text)
    return tuple(normalised)


@dataclass(slots=True)
class _ItemAccumulator:
    name: str
    slot: str
    contexts: set[str]
    variant_ids: set[str]
