"""Integration tests for Alembic migrations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import SQLModel, create_engine

if TYPE_CHECKING:
    from pathlib import Path


def test_alembic_upgrade_creates_tables(tmp_path: Path) -> None:
    db_file = tmp_path / "migrations_test.db"
    db_url = f"sqlite:///{db_file}"

    # Ensure fresh DB
    if db_file.exists():
        db_file.unlink()

    # Run migrations via our helper which wraps alembic
    from d3_item_salvager.scripts.reset_local_db import apply_migrations

    apply_migrations(db_url)

    # After upgrade, tables defined by SQLModel metadata should exist
    engine = create_engine(db_url)
    inspector_tables = (
        engine.connect()
        .connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        .fetchall()
    )
    table_names = {r[0] for r in inspector_tables}

    # expected tables from models
    expected = {t.name for t in SQLModel.metadata.tables.values()}

    assert expected.issubset(table_names)
