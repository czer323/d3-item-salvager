"""initial migration

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-15 00:00:00.000000
"""

from sqlmodel import SQLModel

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use SQLModel metadata to create all tables. Some alembic environments pass a
    # connection that doesn't work with SQLModel's create_all; create an engine
    # from the configured URL to be robust.
    from alembic import context as _context

    url = _context.config.get_main_option("sqlalchemy.url")
    assert url is not None, "alembic.ini must configure sqlalchemy.url for migrations"
    from sqlmodel import create_engine as _create_engine

    engine = _create_engine(url)
    SQLModel.metadata.create_all(bind=engine)


def downgrade() -> None:
    from alembic import context as _context

    url = _context.config.get_main_option("sqlalchemy.url")
    assert url is not None, "alembic.ini must configure sqlalchemy.url for migrations"
    from sqlmodel import create_engine as _create_engine

    engine = _create_engine(url)
    SQLModel.metadata.drop_all(bind=engine)
