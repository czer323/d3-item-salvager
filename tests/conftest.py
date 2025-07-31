"""This module provides fixtures for testing with a temporary SQLite database engine."""

from collections.abc import Generator

import pytest
from sqlalchemy.engine import Engine

from tests.fakes.test_db_utils import temp_db_engine


@pytest.fixture
def sqlite_test_engine() -> Generator[Engine, None, None]:
    """Fixture to provide a temporary SQLite database engine for testing."""
    yield from temp_db_engine()
