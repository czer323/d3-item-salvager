"""Database engine and session setup for Diablo 3 Item Salvager."""

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///d3_items.db"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables() -> None:
    """Create all tables in the database."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a new database session."""
    return Session(engine)
