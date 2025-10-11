"""Unit tests for loader functions using a temporary SQLite database."""

from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.engine import Engine
from sqlmodel import Session

from d3_item_salvager.data.loader import (
    insert_item_usages_with_validation,
    insert_items_from_dict,
)
from d3_item_salvager.data.models import Item, ItemUsage, Profile
from d3_item_salvager.data.queries import (
    get_all_item_usages,
    get_all_items,
    get_item_usages_with_names,
)
from tests.fakes.test_db_utils import insert_sample_data, temp_db_engine

if TYPE_CHECKING:
    from collections.abc import Sequence


@pytest.fixture(name="db_engine")
def db_engine_fixture() -> Generator[Engine, None, None]:
    """Fixture to provide a temporary SQLite database engine for testing."""
    yield from temp_db_engine()


# Test 1: Insert valid items and usages, verify correct DB state and query results
def test_loader_and_queries(db_engine: Engine) -> None:
    """Test that sample data is inserted and query functions return expected results."""
    with Session(db_engine) as session:
        insert_sample_data(session)
        items: Sequence[Item] = get_all_items(session)
        usages: Sequence[ItemUsage] = get_all_item_usages(session)
        usage_with_names: Sequence[tuple[ItemUsage, str]] = get_item_usages_with_names(
            session
        )
        assert len(items) == 1
        assert items[0].name == "Test Sword"
        assert len(usages) == 1
        assert usages[0].slot == "mainhand"
        assert len(usage_with_names) == 1
        usage, name = usage_with_names[0]
        assert name == "Test Sword"
        assert usage.slot == "mainhand"
        assert usage.usage_context == "main"
    db_engine.dispose()


def test_insert_item_missing_fields(db_engine: Engine) -> None:
    """Test 2: Insert item with missing required fields."""
    bad_item: dict[str, str] = {
        "id": "item_002",
        "name": "",
        "type": "weapon",
        "quality": "legendary",
    }
    item_dict: dict[str, dict[str, str]] = {"item_002": bad_item}
    with Session(db_engine) as session:
        with pytest.raises(
            ValueError,
            match=r"Missing required field 'name' in item data:.*",
        ):
            insert_items_from_dict(item_dict, session=session)
        items = get_all_items(session)
        assert all(item.id != "item_002" for item in items)


def test_insert_item_invalid_type_quality(db_engine: Engine) -> None:
    """Test 3: Insert item with invalid type/quality"""
    bad_item: dict[str, str] = {
        "id": "item_003",
        "name": "Bad Item",
        "type": "notatype",
        "quality": "notquality",
    }
    item_dict: dict[str, dict[str, str]] = {"item_003": bad_item}
    with Session(db_engine) as session:
        with pytest.raises(
            ValueError,
            match=r"Invalid item type 'notatype' for item ID 'item_003.'",
        ):
            insert_items_from_dict(item_dict, session=session)
        items = get_all_items(session)
        assert all(item.id != "item_003" for item in items)


def test_insert_duplicate_item_id(db_engine: Engine) -> None:
    """Test 4: Insert duplicate item ID"""
    good_item: dict[str, str] = {
        "id": "item_004",
        "name": "Good Item",
        "type": "spiritstone",
        "quality": "legendary",
    }
    item_dict: dict[str, dict[str, str]] = {"item_004": good_item}
    with Session(db_engine) as session:
        insert_items_from_dict(item_dict, session=session)
        # Second insert should raise ValueError for duplicate
        with pytest.raises(ValueError, match=r"Duplicate item ID 'item_004' detected."):
            insert_items_from_dict(item_dict, session=session)
        items = [item for item in get_all_items(session) if item.id == "item_004"]
        assert len(items) == 1  # Only one should exist


def test_insert_usage_missing_item_id(db_engine: Engine) -> None:
    """Test: Insert usage with missing item_id (not in DB)"""
    with Session(db_engine) as session:
        profile = Profile(build_id=1, name="Sample Profile", class_name="Barbarian")
        session.add(profile)
        session.commit()
        assert profile.id is not None
        bad_usage_item = ItemUsage(
            profile_id=profile.id,
            item_id="bad_id",  # This item_id does not exist in the DB
            slot="mainhand",
            usage_context="main",
        )
        with pytest.raises(ValueError, match=r"Item ID bad_id does not exist."):
            insert_item_usages_with_validation([bad_usage_item], session)
