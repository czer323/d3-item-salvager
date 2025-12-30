"""Unit tests for the item usage aggregation service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from frontend.src.services.item_usage import ItemUsageStatus, build_item_usage_table

if TYPE_CHECKING:  # pragma: no cover - typing aid for fake backend
    from frontend.src.services.backend_client import BackendClient


@dataclass(slots=True)
class _Request:
    path: str


class FakeBackendClient:
    """Simple backend stub returning configured JSON payloads."""

    def __init__(self, responses: dict[str, object]) -> None:
        self._responses = dict(responses)
        self.requests: list[_Request] = []

    def get_json(self, path: str, *, params: dict[str, object] | None = None) -> object:
        _ = params
        self.requests.append(_Request(path=path))
        try:
            return self._responses[path]
        except KeyError as exc:  # pragma: no cover - guard for unexpected paths
            msg = f"Unexpected backend path requested: {path}"
            raise AssertionError(msg) from exc


def test_build_item_usage_table_merges_catalogue_with_usage() -> None:
    """Used items retain usage metadata and unused catalogue entries become salvage."""
    responses: dict[str, object] = {
        "/items": [
            {"id": "item-1", "name": "Mighty Weapon", "slot": "Weapon"},
            {"id": "item-2", "name": "Traveler's Pledge", "slot": "Amulet"},
        ],
        "/build-guides/build-1/variants": [
            {"id": "variant-1", "name": "Primary", "build_guide_id": "build-1"},
        ],
        "/item-usage/variant-1": [
            {
                "item": {"id": "item-1", "name": "Mighty Weapon", "slot": "Weapon"},
                "usage_context": "main",
            }
        ],
    }
    fake_client = FakeBackendClient(responses)
    table = build_item_usage_table(
        cast("BackendClient", fake_client),
        build_ids=("build-1",),
    )

    assert table.total_items == 2
    assert table.used_total == 1
    assert table.salvage_total == 1
    assert tuple(table.available_slots) == ("Amulet", "Weapon")

    rows_by_id = {row.item_id: row for row in table.rows}
    assert set(rows_by_id) == {"item-1", "item-2"}

    used_row = rows_by_id["item-1"]
    assert used_row.status is ItemUsageStatus.USED
    assert used_row.usage_contexts == ("main",)
    assert used_row.variant_ids == ("variant-1",)

    salvage_row = rows_by_id["item-2"]
    assert salvage_row.status is ItemUsageStatus.SALVAGE
    assert salvage_row.usage_contexts == ()
    assert salvage_row.variant_ids == ()

    assert table.selected_build_ids == ("build-1",)

    # The backend should only be queried for the catalogue, variants, and usage.
    requested_paths = {request.path for request in fake_client.requests}
    assert requested_paths == {
        "/items",
        "/build-guides/build-1/variants",
        "/item-usage/variant-1",
    }
