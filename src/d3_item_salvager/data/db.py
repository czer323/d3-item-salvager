"""Database engine and session setup for Diablo 3 Item Salvager."""

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from d3_item_salvager.config.settings import AppConfig, get_config


def get_engine(config: AppConfig | None = None) -> Engine:
    """Create and return a SQLAlchemy engine. Accepts optional config for DI."""
    if config is None:
        config = get_config()
    return create_engine(config.database.url, echo=True)


def create_db_and_tables(config: AppConfig | None = None) -> None:
    """Create all tables in the database. Accepts optional config for DI."""
    engine = get_engine(config)
    SQLModel.metadata.create_all(engine)


def get_session(config: AppConfig | None = None) -> Session:
    """Get a new database session. Accepts optional config for DI."""
    engine = get_engine(config)
    return Session(engine)
