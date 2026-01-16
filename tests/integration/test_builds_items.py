"""Integration tests for /builds/items endpoint (test-first)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from d3_item_salvager.api.dependencies import get_db_session
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

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app)

    yield client, data

    app.dependency_overrides.clear()


def test_builds_items_union_and_ordering(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    client, data = api_client
    build_one = data["builds"]["one"]
    build_two = data["builds"]["two"]

    response = client.get(
        "/builds/items", params={"build_ids": f"{build_one},{build_two}"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total"] == 3
    names = [item["name"] for item in payload["data"]]
    assert names == ["Aquila Cuirass", "Chantodo's Will", "Mighty Weapon"]

    # Each item may include aggregated usage contexts across the requested builds
    by_name = {it["name"]: it for it in payload["data"]}
    assert by_name["Mighty Weapon"]["usage_contexts"] == ["main"]
    assert by_name["Aquila Cuirass"]["usage_contexts"] == ["follower"]
    assert by_name["Chantodo's Will"]["usage_contexts"] == ["kanai"]


def test_builds_items_pagination(api_client: tuple[TestClient, dict[str, Any]]) -> None:
    client, data = api_client
    build_one = data["builds"]["one"]
    build_two = data["builds"]["two"]

    response = client.get(
        "/builds/items",
        params={"build_ids": f"{build_one},{build_two}", "limit": 1, "offset": 1},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total"] == 3
    assert len(payload["data"]) == 1
    assert payload["data"][0]["name"] == "Chantodo's Will"


def test_builds_items_invalid_ids_returns_400(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    client, _ = api_client
    response = client.get("/builds/items", params={"build_ids": "abc"})
    assert response.status_code == 400
