"""Unit tests for query/filter logic in queries.py."""

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from d3_item_salvager.data.models import Build, Profile
from d3_item_salvager.data.queries import (
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
from tests.fakes.test_db_utils import insert_sample_data


def test_get_all_items(sqlite_test_engine: Engine) -> None:
    """Test that get_all_items returns all items in the database.

    Validates that the inserted item is returned and has correct attributes.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        items = get_all_items(session)
        assert len(items) == 1
        assert items[0].name == "Test Sword"


def test_get_all_item_usages(sqlite_test_engine: Engine) -> None:
    """Test that get_all_item_usages returns all item usages in the database.

    Validates that the inserted item usage is returned and has correct slot.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        usages = get_all_item_usages(session)
        assert len(usages) == 1
        assert usages[0].slot == "mainhand"


def test_get_item_usages_with_names(sqlite_test_engine: Engine) -> None:
    """Test that get_item_usages_with_names returns item usages and their names.

    Validates that the returned tuple contains correct usage and item name.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        results = get_item_usages_with_names(session)
        assert len(results) == 1
        usage, name = results[0]
        assert name == "Test Sword"
        assert usage.slot == "mainhand"


def test_get_items_by_class(sqlite_test_engine: Engine) -> None:
    """Test that get_items_by_class filters items by profile class name.

    Validates that only items for the specified class are returned.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        items = get_items_by_class(session, "Barbarian")
        assert len(items) == 1
        assert items[0].name == "Test Sword"


def test_get_items_by_build(sqlite_test_engine: Engine) -> None:
    """Test that get_items_by_build filters items by build ID.

    Validates that only items for the specified build are returned.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        build_id = session.exec(select(Build.id)).first()
        assert build_id is not None
        items = get_items_by_build(session, build_id)
        assert len(items) == 1
        assert items[0].name == "Test Sword"


def test_get_item_usages_by_slot(sqlite_test_engine: Engine) -> None:
    """Test that get_item_usages_by_slot filters usages by slot.

    Validates that only usages for the specified slot are returned.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        usages = get_item_usages_by_slot(session, "mainhand")
        assert len(usages) == 1
        assert usages[0].slot == "mainhand"


def test_get_item_usages_by_context(sqlite_test_engine: Engine) -> None:
    """Test that get_item_usages_by_context filters usages by usage context.

    Validates that only usages for the specified context are returned.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        usages = get_item_usages_by_context(session, "main")
        assert len(usages) == 1
        assert usages[0].usage_context == "main"


def test_get_profiles_for_build(sqlite_test_engine: Engine) -> None:
    """Test that get_profiles_for_build filters profiles by build ID.

    Validates that only profiles for the specified build are returned.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        build_id = session.exec(select(Build.id)).first()
        assert build_id is not None
        profiles = get_profiles_for_build(session, build_id)
        assert len(profiles) == 1
        assert profiles[0].name == "Test Profile"


def test_get_item_usages_for_profile(sqlite_test_engine: Engine) -> None:
    """Test that get_item_usages_for_profile filters usages by profile ID.

    Validates that only usages for the specified profile are returned.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        profile_id = session.exec(select(Profile.id)).first()
        assert profile_id is not None
        usages = get_item_usages_for_profile(session, profile_id)
        assert len(usages) == 1
        assert usages[0].slot == "mainhand"


def test_get_items_for_profile(sqlite_test_engine: Engine) -> None:
    """Test that get_items_for_profile filters items by profile ID.

    Validates that only items for the specified profile are returned.
    """
    with Session(sqlite_test_engine) as session:
        insert_sample_data(session)
        profile_id = session.exec(select(Profile.id)).first()
        assert profile_id is not None
        items = get_items_for_profile(session, profile_id)
        assert len(items) == 1
        assert items[0].name == "Test Sword"
