"""Aggregate backend responses into variant summary objects."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass
from typing import Any

from flask import current_app

from frontend.src.services.backend_client import (
    BackendClient,
    BackendClientError,
    BackendResponseError,
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

    @property
    def usage_label(self) -> str:
        """Readable usage label summarising contexts."""
        return ", ".join(context.title() for context in self.usage_contexts)

    @property
    def badge_class(self) -> str:
        """Return a Tailwind/DaisyUI badge class for this classification."""
        return _BADGE_MAP[self.classification]

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
    """Aggregate of used and salvageable items for a variant."""

    variant: VariantDetails
    used_items: list[ItemSummary]
    salvage_items: list[ItemSummary]

    def to_contract_payload(self) -> dict[str, Any]:
        """Return JSON payload adhering to the documented contract."""
        return {
            "variant": asdict(self.variant),
            "items": [
                *[item.to_contract_entry() for item in self.used_items],
                *[item.to_contract_entry() for item in self.salvage_items],
            ],
        }


def build_variant_summary(client: BackendClient, variant_id: str) -> VariantSummary:
    """Fetch backend data and compose a variant summary."""
    variant = _fetch_variant_details(client, variant_id)
    usage_rows = client.get_json(f"/item-usage/{variant_id}")
    if not isinstance(usage_rows, list):
        msg = "Expected backend to return a list of usage rows"
        raise BackendResponseError(msg)

    deduped: OrderedDict[str, ItemSummary] = OrderedDict()
    usage_tracker: dict[str, set[str]] = {}
    for row in usage_rows:
        if not isinstance(row, dict):
            current_app.logger.debug("Skipping non-dict usage row: %s", row)
            continue
        item = row.get("item", {})
        if not isinstance(item, dict):
            current_app.logger.debug("Skipping usage row without item payload: %s", row)
            continue
        item_id = str(item.get("id", ""))
        if not item_id:
            current_app.logger.debug("Skipping malformed usage row: %s", row)
            continue
        name = str(item.get("name", "Unknown Item"))
        slot = str(item.get("slot", "Unknown"))
        context = str(row.get("usage_context", "unknown")).lower()

        if item_id not in deduped:
            usage_tracker[item_id] = {context}
            deduped[item_id] = ItemSummary(
                item_id=item_id,
                name=name,
                slot=slot,
                usage_contexts=(context,),
                classification=SalvageLabel.KEEP,
            )
        else:
            usage_tracker[item_id].add(context)

    used_items: list[ItemSummary] = []
    salvage_items: list[ItemSummary] = []
    for item_id, summary in deduped.items():
        contexts = tuple(sorted(usage_tracker[item_id]))
        classification = classify_usage_contexts(contexts)
        updated = ItemSummary(
            item_id=item_id,
            name=summary.name,
            slot=summary.slot,
            usage_contexts=contexts,
            classification=classification,
        )
        if classification is SalvageLabel.SALVAGE:
            salvage_items.append(updated)
        else:
            used_items.append(updated)

    return VariantSummary(
        variant=variant, used_items=used_items, salvage_items=salvage_items
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
