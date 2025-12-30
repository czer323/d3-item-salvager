"""Contract tests for the variant JSON endpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from frontend.src.services.backend_client import BackendClient

SCHEMA_PATH = (
    Path(__file__)
    .resolve()
    .parents[3]
    .joinpath("specs", "001-design-a-frontend", "contracts", "variant.json")
)


@pytest.fixture(name="schema")
def schema_fixture() -> dict[str, Any]:
    """Load the OpenAPI contract for the variant endpoint."""
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(name="stub_backend", autouse=True)
def stub_backend_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub backend client responses so the frontend can build a summary."""
    sample_variant = {
        "id": "test-variant",
        "name": "Test Variant",
        "build_guide_id": "guide-123",
    }

    sample_usage = [
        {
            "item_id": "item-1",
            "usage_context": "main",
            "item": {
                "id": "item-1",
                "name": "Mighty Axe",
                "slot": "Weapon",
            },
        },
        {
            "item_id": "item-2",
            "usage_context": "unused",
            "item": {
                "id": "item-2",
                "name": "Rusty Boots",
                "slot": "Boots",
            },
        },
    ]

    def fake_get_json(
        _self: BackendClient, path: str, *, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]] | dict[str, str]:
        _ = params
        if path == "/item-usage/test-variant":
            return sample_usage
        if path == "/variants/test-variant":
            return sample_variant
        msg = f"Unexpected backend path requested: {path}"
        raise AssertionError(msg)

    monkeypatch.setattr(BackendClient, "get_json", fake_get_json)


def _assert_variant_contract(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate payload structure matches required schema properties."""
    assert "variant" in payload, "variant object missing from response"
    assert "items" in payload, "items list missing from response"

    variant_schema = schema["components"]["schemas"]["Variant"]
    required_variant_fields = set(variant_schema["required"])
    variant = payload["variant"]
    assert required_variant_fields.issubset(variant.keys())

    item_schema = schema["components"]["schemas"]["ItemUsage"]
    required_item_fields = set(item_schema["required"])
    items: list[dict[str, Any]] = payload["items"]
    assert isinstance(items, list)
    assert items, "items payload should not be empty"

    for entry in items:
        assert isinstance(entry, dict)
        assert required_item_fields.issubset(entry.keys())
        item_details = cast("dict[str, Any]", entry["item"])
        nested_required = set(item_schema["properties"]["item"]["required"])
        assert nested_required.issubset(set(item_details))


if TYPE_CHECKING:
    from flask.testing import FlaskClient
else:  # pragma: no cover - runtime fallback for type checking only import
    FlaskClient = Any  # type: ignore[assignment]


@pytest.mark.usefixtures("frontend_app")
def test_variant_endpoint_matches_contract(
    client: FlaskClient, schema: dict[str, Any]
) -> None:
    """Response payload must satisfy the documented OpenAPI contract."""
    response = client.get("/frontend/variant/test-variant.json")
    assert response.status_code == 200
    payload = cast("dict[str, Any]", response.get_json())
    _assert_variant_contract(payload, schema)
