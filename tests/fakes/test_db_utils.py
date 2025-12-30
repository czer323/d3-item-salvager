"""Shared test utilities for temporary database and sample data insertion."""

import os
import tempfile
from collections.abc import Generator
from typing import Any

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from d3_item_salvager.data.models import Build, Item, ItemUsage, Profile


def temp_db_engine() -> Generator[Engine, None, None]:
    """Create a temporary SQLite database and yield its engine."""
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
    assert build.id is not None, "Build id cannot be None"
    profile = Profile(build_id=build.id, name="Test Profile", class_name="Barbarian")
    session.add(profile)
    session.commit()
    session.refresh(profile)
    item = Item(id="item_001", name="Test Sword", type="weapon", quality="legendary")
    session.add(item)
    session.commit()
    assert profile.id is not None, "Profile id cannot be None"
    usage = ItemUsage(
        profile_id=profile.id, item_id=item.id, slot="mainhand", usage_context="main"
    )
    session.add(usage)
    session.commit()


def seed_salvage_dataset(session: Session) -> dict[str, Any]:
    """Insert a representative salvage dataset and return identifiers."""
    build_one = Build(title="Guide One", url="https://example.com/one")
    build_two = Build(title="Guide Two", url="https://example.com/two")
    session.add(build_one)
    session.add(build_two)
    session.commit()
    session.refresh(build_one)
    session.refresh(build_two)
    build_one_id = build_one.id
    build_two_id = build_two.id
    assert build_one_id is not None
    assert build_two_id is not None

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
    profile_a_id = profile_a.id
    profile_b_id = profile_b.id
    profile_c_id = profile_c.id
    assert profile_a_id is not None
    assert profile_b_id is not None
    assert profile_c_id is not None

    item_one = Item(
        id="item_001",
        name="Mighty Weapon",
        type="mainhand",
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
        type="mainhand",
        quality="set",
    )
    session.add(item_one)
    session.add(item_two)
    session.add(item_three)
    session.commit()

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
    usage_a_id = usage_a.id
    usage_b_id = usage_b.id
    usage_c_id = usage_c.id
    assert usage_a_id is not None
    assert usage_b_id is not None
    assert usage_c_id is not None

    return {
        "builds": {
            "one": build_one_id,
            "two": build_two_id,
        },
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
