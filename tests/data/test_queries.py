"""Unit tests for query/filter logic in queries.py."""

import os
import tempfile
from collections.abc import Generator

import pytest
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from src.d3_item_salvager.data.models import Build, Item, ItemUsage, Profile
from src.d3_item_salvager.data.queries import (
    get_all_item_usages,
    get_all_items,
    get_item_usages_by_context,
    get_item_usages_by_slot,
    get_item_usages_for_profile,
    get_item_usages_with_names,
    get_items_by_build,
    get_items_by_class,
    get_items_for_profile,
    get_profiles_for_build,
)


@pytest.fixture(name="db_engine")
def temp_db() -> Generator[Engine, None, None]:
    """Fixture to create a temporary SQLite database for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()
    os.close(db_fd)
    os.remove(db_path)


def insert_sample_data(session: Session) -> None:
    """Insert sample data into the database for testing."""
    build = Build(title="Test Build", url="https://example.com/build")
    session.add(build)
    session.commit()
    session.refresh(build)
    profile = Profile(build_id=build.id, name="Test Profile", class_name="Barbarian")
    session.add(profile)
    session.commit()
    session.refresh(profile)
    item = Item(id="item_001", name="Test Sword", type="weapon", quality="legendary")
    session.add(item)
    session.commit()
    usage = ItemUsage(
        profile_id=profile.id, item_id=item.id, slot="mainhand", usage_context="main"
    )
    session.add(usage)
    session.commit()


def test_get_all_items(db_engine: Engine) -> None:
    """Test that get_all_items returns all items in the database.

    Validates that the inserted item is returned and has correct attributes.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        items = get_all_items(session)
        assert len(items) == 1
        assert items[0].name == "Test Sword"


def test_get_all_item_usages(db_engine: Engine) -> None:
    """Test that get_all_item_usages returns all item usages in the database.

    Validates that the inserted item usage is returned and has correct slot.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        usages = get_all_item_usages(session)
        assert len(usages) == 1
        assert usages[0].slot == "mainhand"


def test_get_item_usages_with_names(db_engine: Engine) -> None:
    """Test that get_item_usages_with_names returns item usages and their names.

    Validates that the returned tuple contains correct usage and item name.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        results = get_item_usages_with_names(session)
        assert len(results) == 1
        usage, name = results[0]
        assert name == "Test Sword"
        assert usage.slot == "mainhand"


def test_get_items_by_class(db_engine: Engine) -> None:
    """Test that get_items_by_class filters items by profile class name.

    Validates that only items for the specified class are returned.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        items = get_items_by_class(session, "Barbarian")
        assert len(items) == 1
        assert items[0].name == "Test Sword"


def test_get_items_by_build(db_engine: Engine) -> None:
    """Test that get_items_by_build filters items by build ID.

    Validates that only items for the specified build are returned.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        build_id = session.exec(select(Build.id)).first()
        assert build_id is not None
        items = get_items_by_build(session, build_id)
        assert len(items) == 1
        assert items[0].name == "Test Sword"


def test_get_item_usages_by_slot(db_engine: Engine) -> None:
    """Test that get_item_usages_by_slot filters usages by slot.

    Validates that only usages for the specified slot are returned.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        usages = get_item_usages_by_slot(session, "mainhand")
        assert len(usages) == 1
        assert usages[0].slot == "mainhand"


def test_get_item_usages_by_context(db_engine: Engine) -> None:
    """Test that get_item_usages_by_context filters usages by usage context.

    Validates that only usages for the specified context are returned.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        usages = get_item_usages_by_context(session, "main")
        assert len(usages) == 1
        assert usages[0].usage_context == "main"


def test_get_profiles_for_build(db_engine: Engine) -> None:
    """Test that get_profiles_for_build filters profiles by build ID.

    Validates that only profiles for the specified build are returned.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        build_id = session.exec(select(Build.id)).first()
        assert build_id is not None
        profiles = get_profiles_for_build(session, build_id)
        assert len(profiles) == 1
        assert profiles[0].name == "Test Profile"


def test_get_item_usages_for_profile(db_engine: Engine) -> None:
    """Test that get_item_usages_for_profile filters usages by profile ID.

    Validates that only usages for the specified profile are returned.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        profile_id = session.exec(select(Profile.id)).first()
        assert profile_id is not None
        usages = get_item_usages_for_profile(session, profile_id)
        assert len(usages) == 1
        assert usages[0].slot == "mainhand"


def test_get_items_for_profile(db_engine: Engine) -> None:
    """Test that get_items_for_profile filters items by profile ID.

    Validates that only items for the specified profile are returned.
    """
    with Session(db_engine) as session:
        insert_sample_data(session)
        profile_id = session.exec(select(Profile.id)).first()
        assert profile_id is not None
        items = get_items_for_profile(session, profile_id)
        assert len(items) == 1
        assert items[0].name == "Test Sword"
