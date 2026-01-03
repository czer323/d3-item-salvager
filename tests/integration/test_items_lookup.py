"""Integration tests for /items/lookup endpoint (test-first)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from d3_item_salvager.api.factory import create_app
from tests.fakes.test_db_utils import seed_salvage_dataset


@pytest.fixture
def api_client(
    sqlite_test_engine: Engine,
) -> Generator[tuple[TestClient, dict[str, Any]], None, None]:
    engine = sqlite_test_engine
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        data = seed_salvage_dataset(session)

    app = create_app()

    from d3_item_salvager.api.dependencies import get_db_session

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app)

    yield client, data

    app.dependency_overrides.clear()


def test_items_lookup_exact_match(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    client, data = api_client
    response = client.get("/items/lookup", params={"query": "Mighty Weapon"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["match_type"] == "exact"
    assert payload["item"]["id"] == data["items"]["weapon"]
    assert payload["salvageable"] is False


def test_items_lookup_fuzzy_suggestions(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    client, data = api_client
    # Intentional typo to exercise fuzzy matching
    response = client.get("/items/lookup", params={"query": "Mighy"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["match_type"] == "fuzzy"
    assert payload["item"] is None
    # suggestions should include the weapon id
    suggestion_ids = [s["id"] for s in payload["suggestions"]]
    assert data["items"]["weapon"] in suggestion_ids
    assert payload["salvageable"] is False


def test_items_lookup_none_returns_salvageable(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    client, _ = api_client
    response = client.get("/items/lookup", params={"query": "This Item Does Not Exist"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["match_type"] == "none"
    assert payload["item"] is None
    assert payload["suggestions"] == []
    assert payload["salvageable"] is True
