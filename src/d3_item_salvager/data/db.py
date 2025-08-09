"""Database engine and session setup for Diablo 3 Item Salvager."""

from sqlalchemy.engine import Engine
from sqlmodel import SQLModel


def create_db_and_tables(engine: Engine) -> None:
    """Create all tables in the database."""
    SQLModel.metadata.create_all(engine)
