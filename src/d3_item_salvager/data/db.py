"""Database engine and session setup for Diablo 3 Item Salvager."""

from sqlmodel import Session, SQLModel, create_engine

from d3_item_salvager.config import get_config

config = get_config()
engine = create_engine(config.database.url, echo=True)


def create_db_and_tables() -> None:
    """Create all tables in the database."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a new database session."""
    return Session(engine)
