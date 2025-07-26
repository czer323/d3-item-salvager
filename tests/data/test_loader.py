"""Unit tests for loader functions using a temporary SQLite database."""

import os
import tempfile
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from src.d3_item_salvager.data.loader import (
    insert_item_usages_with_validation,
    insert_items_from_dict,
)
from src.d3_item_salvager.data.models import Build, Item, ItemUsage, Profile
from src.d3_item_salvager.data.queries import (
    get_all_item_usages,
    get_all_items,
    get_item_usages_with_names,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


@pytest.fixture(name="db_engine")
def temp_db() -> Generator[Engine, None, None]:
    """Create a temporary SQLite database and yield its engine."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()
    os.close(db_fd)
    os.remove(db_path)


def insert_sample_data(engine: Engine) -> None:
    """Insert sample builds, profiles, items, and item usages into the database."""
    with Session(engine) as session:
        build = Build(title="Sample Build", url="https://example.com/build")
        session.add(build)
        session.commit()
        session.refresh(build)

        profile = Profile(
            build_id=build.id, name="Sample Profile", class_name="Barbarian"
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)

        item = Item(
            id="item_001", name="Sample Sword", type="weapon", quality="legendary"
        )
        session.add(item)
        session.commit()

        usage = ItemUsage(
            profile_id=profile.id,
            item_id=item.id,
            slot="mainhand",
            usage_context="main",
        )
        session.add(usage)
        session.commit()


# Test 1: Insert valid items and usages, verify correct DB state and query results
def test_loader_and_queries(db_engine: Engine) -> None:
    """Test that sample data is inserted and query functions return expected results."""
    insert_sample_data(db_engine)
    with Session(db_engine) as session:
        items: Sequence[Item] = get_all_items(session)
        usages: Sequence[ItemUsage] = get_all_item_usages(session)
        usage_with_names: Sequence[tuple[ItemUsage, str]] = get_item_usages_with_names(
            session
        )
        assert len(items) == 1
        assert items[0].name == "Sample Sword"
        assert len(usages) == 1
        assert usages[0].slot == "mainhand"
        assert len(usage_with_names) == 1
        usage, name = usage_with_names[0]
        assert name == "Sample Sword"
        assert usage.slot == "mainhand"
        assert usage.usage_context == "main"
    db_engine.dispose()


def test_insert_item_missing_fields(
    db_engine: Engine, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test 2: Insert item with missing required fields."""
    bad_item = {"id": "item_002", "name": "", "type": "weapon", "quality": "legendary"}
    item_dict = {"item_002": bad_item}
    with Session(db_engine) as session:
        insert_items_from_dict(item_dict, session=session)
        captured = capsys.readouterr()
        assert (
            "Missing required field" in captured.out
            or "Validation error" in captured.out
        )
        items = get_all_items(session)
        assert all(item.id != "item_002" for item in items)


def test_insert_item_invalid_type_quality(
    db_engine: Engine, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test 3: Insert item with invalid type/quality"""
    bad_item = {
        "id": "item_003",
        "name": "Bad Item",
        "type": "notatype",
        "quality": "notquality",
    }
    item_dict = {"item_003": bad_item}
    with Session(db_engine) as session:
        insert_items_from_dict(item_dict, session=session)
        captured = capsys.readouterr()
        assert (
            "Invalid item type" in captured.out
            or "Invalid item quality" in captured.out
        )
        items = get_all_items(session)
        assert all(item.id != "item_003" for item in items)


def test_insert_duplicate_item_id(db_engine: Engine) -> None:
    """Test 4: Insert duplicate item ID"""
    good_item = {
        "id": "item_004",
        "name": "Good Item",
        "type": "weapon",
        "quality": "legendary",
    }
    item_dict = {"item_004": good_item}
    with Session(db_engine) as session:
        insert_items_from_dict(item_dict, session=session)
        # Try to insert again
        insert_items_from_dict(item_dict, session=session)
        items = [item for item in get_all_items(session) if item.id == "item_004"]
        assert len(items) == 1  # Only one should exist


def test_insert_usage_missing_profile_or_item(db_engine: Engine) -> None:
    """Test 5: Insert usage with missing profile_id/item_id"""
    with Session(db_engine) as session:
        # No profiles/items exist yet
        bad_usage = {
            "profile_id": 999,
            "item_id": "bad_id",
            "slot": "mainhand",
            "usage_context": "main",
        }
        with pytest.raises(
            ValueError,
            match="Profile ID 999 does not exist.|Item ID bad_id does not exist.",
        ):
            insert_item_usages_with_validation([bad_usage], session)
