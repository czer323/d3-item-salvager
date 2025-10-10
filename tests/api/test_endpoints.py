"""API endpoint tests covering list endpoints and filtering."""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel

from d3_item_salvager.api.dependencies import get_db_session
from d3_item_salvager.api.factory import create_app
from d3_item_salvager.data.models import Build, Item, ItemUsage, Profile


def _seed_database(session: Session) -> dict[str, Any]:
    """Insert representative data and return created identifiers."""
    build_one = Build(title="Guide One", url="https://example.com/one")
    build_two = Build(title="Guide Two", url="https://example.com/two")
    session.add(build_one)
    session.add(build_two)
    session.commit()
    session.refresh(build_one)
    session.refresh(build_two)
    assert build_one.id is not None
    assert build_two.id is not None

    build_one_id = build_one.id
    build_two_id = build_two.id

    profile_a = Profile(
        build_id=build_one_id,
        name="Leapquake",
        class_name="Barbarian",
    )
    profile_b = Profile(
        build_id=build_one_id,
        name="Support",
        class_name="Barbarian",
    )
    profile_c = Profile(
        build_id=build_two_id,
        name="Archon",
        class_name="Wizard",
    )
    session.add(profile_a)
    session.add(profile_b)
    session.add(profile_c)
    session.commit()
    session.refresh(profile_a)
    session.refresh(profile_b)
    session.refresh(profile_c)
    assert profile_a.id is not None
    assert profile_b.id is not None
    assert profile_c.id is not None

    item_one = Item(
        id="item_001",
        name="Mighty Weapon",
        type="weapon",
        quality="set",
    )
    item_two = Item(
        id="item_002",
        name="Aquila Cuirass",
        type="chest",
        quality="legendary",
    )
    item_three = Item(
        id="item_003",
        name="Chantodo's Will",
        type="weapon",
        quality="set",
    )
    session.add(item_one)
    session.add(item_two)
    session.add(item_three)
    session.commit()

    profile_a_id = profile_a.id
    profile_b_id = profile_b.id
    profile_c_id = profile_c.id

    usage_a = ItemUsage(
        profile_id=profile_a_id,
        item_id=item_one.id,
        slot="mainhand",
        usage_context="main",
    )
    usage_b = ItemUsage(
        profile_id=profile_b_id,
        item_id=item_two.id,
        slot="chest",
        usage_context="follower",
    )
    usage_c = ItemUsage(
        profile_id=profile_c_id,
        item_id=item_three.id,
        slot="mainhand",
        usage_context="kanai",
    )
    session.add(usage_a)
    session.add(usage_b)
    session.add(usage_c)
    session.commit()
    session.refresh(usage_a)
    session.refresh(usage_b)
    session.refresh(usage_c)
    assert usage_a.id is not None
    assert usage_b.id is not None
    assert usage_c.id is not None
    usage_a_id = usage_a.id
    usage_b_id = usage_b.id
    usage_c_id = usage_c.id

    return {
        "builds": {"one": build_one_id, "two": build_two_id},
        "profiles": {
            "leapquake": profile_a_id,
            "support": profile_b_id,
            "archon": profile_c_id,
        },
        "items": {
            "weapon": item_one.id,
            "chest": item_two.id,
            "wand": item_three.id,
        },
        "usages": {
            "main": usage_a_id,
            "follower": usage_b_id,
            "kanai": usage_c_id,
        },
    }


@pytest.fixture
def api_client(
    sqlite_test_engine: Engine,
) -> Generator[tuple[TestClient, dict[str, Any]], None, None]:
    """Provide a test client with seeded database and captured identifiers."""
    engine = sqlite_test_engine
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        data = _seed_database(session)

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
