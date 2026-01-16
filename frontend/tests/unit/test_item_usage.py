"""Unit tests for the item usage aggregation service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from frontend.src.services.item_usage import build_item_usage_table

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
    """Only catalogue items used in the selected builds are returned."""
    responses: dict[str, object] = {
        "/items": [
            {"id": "item-1", "name": "Mighty Weapon", "slot": "Weapon"},
            {"id": "item-2", "name": "Traveler's Pledge", "slot": "Amulet"},
        ],
        "/build-guides/build-1/variants": [
            {"id": "variant-1", "name": "Primary", "build_guide_id": "build-1"},
            {"id": "variant-2", "name": "Support", "build_guide_id": "build-1"},
        ],
        "/item-usage/variant-1": [
            {
                "item": {"id": "item-1", "name": "Mighty Weapon", "slot": "Weapon"},
                "usage_context": "main",
            }
        ],
        "/item-usage/variant-2": [
            {
                "item": {"id": "item-1", "name": "Mighty Weapon", "slot": "Weapon"},
                "usage_context": "follower",
            }
        ],
    }
    fake_client = FakeBackendClient(responses)
    table = build_item_usage_table(
        cast("BackendClient", fake_client),
        build_ids=("build-1",),
    )

    assert table.total_items == 1
    assert table.used_total == 1
    assert tuple(table.available_slots) == ("Weapon",)

    rows_by_id = {row.item_id: row for row in table.rows}
    assert set(rows_by_id) == {"item-1"}

    used_row = rows_by_id["item-1"]
    assert used_row.is_used
    assert used_row.usage_contexts == ("main", "follower"), (
        "Expected contexts ordered as main, follower"
    )
    assert used_row.variant_ids == ("variant-1", "variant-2")

    assert table.selected_build_ids == ("build-1",)

    # The backend should only be queried for the catalogue, variants, and usage.
    requested_paths = {request.path for request in fake_client.requests}
    assert requested_paths == {
        "/items",
        "/build-guides/build-1/variants",
        "/item-usage/variant-1",
        "/item-usage/variant-2",
    }
