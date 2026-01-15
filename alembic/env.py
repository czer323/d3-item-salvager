import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    import contextlib

    # Some environments provide a minimal alembic.ini without full logging
    # sections. Avoid failing on logging configuration in tests by suppressing
    # logging config errors.
    with contextlib.suppress(Exception):
        fileConfig(config.config_file_name)

# Ensure models are importable so SQLModel metadata is populated for autogenerate
import contextlib
import importlib
import sys
from pathlib import Path

from sqlmodel import SQLModel

# Ensure project's `src/` is on sys.path so imports like
# ``d3_item_salvager.data.models`` work when Alembic runs inside
# test/CI environments where Pythonpath may not be configured.
proj_root = Path(__file__).resolve().parents[1]
src_path = str(proj_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import models to populate SQLModel metadata. If this fails, surface a
# clear error rather than silently proceeding with empty metadata.
try:
    _ = importlib.import_module("d3_item_salvager.data.models")
except Exception as exc:  # pragma: no cover - surface errors only in misconfigured envs
    msg = "Failed to import project models for Alembic autogenerate; ensure 'src' is on PYTHONPATH"
    raise RuntimeError(msg) from exc


target_metadata = SQLModel.metadata

# Override sqlalchemy.url from env if provided
db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from typing import Any, cast

    cfg_section_raw = config.get_section(config.config_ini_section) or {}
    cfg_section = cast("dict[str, Any]", cfg_section_raw)

    connectable = engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
