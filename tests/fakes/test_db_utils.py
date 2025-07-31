"""Shared test utilities for temporary database and sample data insertion."""

import os
import tempfile
from collections.abc import Generator

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
