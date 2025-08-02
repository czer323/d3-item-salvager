"""Dependency provider functions for config, DB, and services."""

from sqlalchemy.engine import Engine
from sqlmodel import Session

from d3_item_salvager.config.settings import AppConfig, get_config
from d3_item_salvager.data.db import get_engine, get_session


def provide_config(config: AppConfig | None = None) -> AppConfig:
    """Return AppConfig, using DI or default."""
    return config if config is not None else get_config()


def provide_db_engine(config: AppConfig | None = None) -> Engine:
    """Return SQLAlchemy engine using config."""
    return get_engine(config)


def provide_db_session(config: AppConfig | None = None) -> Session:
    """Return SQLModel session using config."""
    return get_session(config)


# Add service providers here as needed
