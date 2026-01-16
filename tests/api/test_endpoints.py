"""API endpoint tests covering list endpoints and filtering."""

from collections.abc import Generator
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel

from d3_item_salvager.api.dependencies import get_db_session
from d3_item_salvager.api.factory import create_app
from d3_item_salvager.data import queries
from tests.fakes.test_db_utils import seed_salvage_dataset


@pytest.fixture
def api_client(
    sqlite_test_engine: Engine,
) -> Generator[tuple[TestClient, dict[str, Any]], None, None]:
    """Provide a test client with seeded database and captured identifiers."""
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


def test_list_items_filters_by_class_and_usage(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Items endpoint filters by class and usage context with pagination metadata."""
    client, data = api_client
    response = client.get(
        "/items",
        params={
            "class_name": "Wizard",
            "usage_context": "kanai",
            "limit": 5,
            "offset": 0,
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["meta"] == {"limit": 5, "offset": 0, "total": 1}
    ids = [item["id"] for item in payload["data"]]
    assert ids == [data["items"]["wand"]]


def test_list_builds_respects_pagination(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Builds endpoint applies limit/offset pagination ordering by title."""
    client, _ = api_client
    response = client.get("/builds", params={"limit": 1, "offset": 1})
    payload = response.json()
    assert response.status_code == 200
    assert payload["meta"]["total"] == 2
    assert len(payload["data"]) == 1
    assert payload["data"][0]["title"] == "Guide Two"


def test_list_profiles_filters_by_build(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Profiles endpoint filters by build id and class."""
    client, data = api_client
    response = client.get(
        "/profiles",
        params={
            "build_id": data["builds"]["one"],
            "class_name": "Barbarian",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["meta"]["total"] == 2
    names = [profile["name"] for profile in payload["data"]]
    assert names == ["Leapquake", "Support"]


def test_list_item_usages_filters_by_item(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Item usages endpoint filters by item id and usage context."""
    client, data = api_client
    response = client.get(
        "/item_usages",
        params={
            "item_id": data["items"]["weapon"],
            "usage_context": "main",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["meta"]["total"] == 1
    assert payload["data"][0]["item_id"] == data["items"]["weapon"]


def test_build_guides_endpoint_exposes_class_metadata(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Build guides endpoint includes aggregated class metadata."""
    client, _ = api_client
    response = client.get("/build-guides")
    assert response.status_code == 200
    payload = response.json()
    guides = payload["data"]
    assert len(guides) == 2
    assert {guide["class_name"] for guide in guides} == {"Barbarian", "Wizard"}


def test_build_variants_endpoint_returns_profiles(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Variant listing returns profiles for a build guide."""
    client, data = api_client
    build_id = data["builds"]["one"]
    response = client.get(f"/build-guides/{build_id}/variants")
    assert response.status_code == 200
    payload = response.json()
    variants = payload["data"]
    assert {variant["name"] for variant in variants} == {"Leapquake", "Support"}
    assert all(variant["build_guide_id"] == build_id for variant in variants)


def test_variant_detail_endpoint_returns_single_profile(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Variant detail endpoint returns a single profile payload."""
    client, data = api_client
    profile_id = data["profiles"]["leapquake"]
    response = client.get(f"/variants/{profile_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == profile_id
    assert payload["name"] == "Leapquake"


def test_item_usage_variant_endpoint_returns_nested_items(
    api_client: tuple[TestClient, dict[str, Any]],
    sqlite_test_engine: Engine,
) -> None:
    """Item usage endpoint returns nested item metadata for a variant."""
    client, data = api_client
    profile_id = data["profiles"]["leapquake"]

    # Sanity-check the DB row contains the expected quality value
    with Session(sqlite_test_engine) as session:
        rows = queries.list_item_usage_with_items(session, profile_id)
        assert rows, "expected ORM rows for profile"
        _, item_obj = rows[0]
        assert getattr(item_obj, "quality", None) == "set", (
            "Expected DB item to have quality 'set'"
        )

    response = client.get(f"/item-usage/{profile_id}")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload, "expected non-empty payload list"
    # Find the entry for the expected item and assert its metadata
    entry: dict[str, Any] | None = None
    from typing import cast as _cast

    for p in cast("list[dict[str, Any]]", payload):
        item_raw = p.get("item")
        if isinstance(item_raw, dict):
            item = _cast("dict[str, Any]", item_raw)
            if item.get("name") == "Mighty Weapon":
                entry = p
                break

    assert entry is not None, "Expected an item usage entry for 'Mighty Weapon'"
    assert entry["item"]["slot"] == "mainhand"
    assert entry["item"].get("quality") == "set"


def test_variant_detail_endpoint_returns_404_when_missing(
    api_client: tuple[TestClient, dict[str, Any]],
) -> None:
    """Variant detail endpoint returns 404 for missing profile id."""
    client, _ = api_client
    response = client.get("/variants/99999")
    assert response.status_code == 404
