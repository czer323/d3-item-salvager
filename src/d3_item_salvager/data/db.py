"""Database engine and session setup for Diablo 3 Item Salvager."""

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from d3_item_salvager.config import get_config


def get_engine() -> Engine:
    """Create and return a SQLAlchemy engine."""
    config = get_config()
    return create_engine(config.database.url, echo=True)


def create_db_and_tables() -> None:
    """Create all tables in the database."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a new database session."""
    engine = get_engine()
    return Session(engine)
