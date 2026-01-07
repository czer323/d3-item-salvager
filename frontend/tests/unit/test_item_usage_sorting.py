from __future__ import annotations

from typing import TYPE_CHECKING

from frontend.src.services.item_usage import build_item_usage_table

if TYPE_CHECKING:
    from frontend.src.services.backend_client import BackendClient


def test_build_item_usage_table_sorts_by_name_and_item_id(
    patched_item_usage_loaders: object, backend_client: BackendClient
) -> None:
    # patched_item_usage_loaders fixture is used for its side-effects (monkeypatching)
    del patched_item_usage_loaders

    table = build_item_usage_table(backend_client, build_ids=["1"])
    assert [r.item_id for r in table.rows] == ["a", "b", "c"]
    assert [r.name.lower() for r in table.rows] == ["alpha", "alpha", "beta"]
