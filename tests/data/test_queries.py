"""Unit tests for query/filter logic in queries.py."""

import pytest
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


def test_list_build_guides_with_classes_picks_most_common(
    sqlite_test_engine: Engine,
) -> None:
    """When a build has profiles with mixed classes, the most common normalized class is chosen."""
    from d3_item_salvager.data.models import Build, Profile
    from d3_item_salvager.data.queries import list_build_guides_with_classes
    from d3_item_salvager.utility.class_names import normalize_class_name

    with Session(sqlite_test_engine) as session:
        # Create a build and mixed profiles
        build = Build(title="Mixed Guide", url="/mixed")
        session.add(build)
        session.commit()
        session.refresh(build)
        # Ensure build.id is present before using it for profile foreign keys
        assert build.id is not None
        b_id = build.id
        session.add_all(
            [
                Profile(build_id=b_id, name="A", class_name="demonhunter"),
                Profile(build_id=b_id, name="B", class_name="demonhunter"),
                Profile(build_id=b_id, name="C", class_name="Wizard"),
            ]
        )
        session.commit()

        rows = list_build_guides_with_classes(session)
        found = [r for r in rows if r[0].title == "Mixed Guide"]
        assert len(found) == 1
        _, class_name = found[0]
        assert class_name == normalize_class_name("demonhunter")


def test_list_build_guides_with_classes_none_when_no_profiles(
    sqlite_test_engine: Engine,
) -> None:
    """Builds with no profiles report None for class_name."""
    from d3_item_salvager.data.models import Build
    from d3_item_salvager.data.queries import list_build_guides_with_classes

    with Session(sqlite_test_engine) as session:
        build = Build(title="Lonely Guide", url="/lonely")
        session.add(build)
        session.commit()

        rows = list_build_guides_with_classes(session)
        found = [r for r in rows if r[0].title == "Lonely Guide"]
        assert len(found) == 1
        _, class_name = found[0]
        assert class_name is None


def test_list_build_guides_with_classes_asserts_on_none_id() -> None:
    """If a Build with None id is encountered from query rows, an assertion is raised."""
    from typing import cast

    from d3_item_salvager.data.models import Build
    from d3_item_salvager.data.queries import list_build_guides_with_classes

    class FakeResult:
        def __init__(self, rows: list[tuple[Build, str]]) -> None:
            self._rows = rows

        def all(self) -> list[tuple[Build, str]]:
            return self._rows

    class FakeSession:
        def exec(self, _stmt: object) -> FakeResult:
            # Return a Build object with id None to simulate a transient object in rows
            b = Build(title="Transient", url="/t")
            b.id = None
            return FakeResult([(b, "Wizard")])

    with pytest.raises(AssertionError, match="Expected persisted Build records"):
        list_build_guides_with_classes(cast("Session", FakeSession()))
