"""Unit test for FastAPI /health endpoint in factory.py."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from d3_item_salvager.api.dependencies import get_config, get_db_session, get_service
from d3_item_salvager.api.factory import create_app
from d3_item_salvager.config.base import (
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
)
from d3_item_salvager.config.settings import AppConfig


@pytest.fixture
def test_config() -> AppConfig:
    """Fixture for DummyConfig used in dependency overrides."""
    return AppConfig(
        app_name="TestApp",
        database=DatabaseConfig(url="sqlite:///:memory:"),
        maxroll_parser=MaxrollParserConfig(bearer_token="dummy-token"),
        logging=LoggingConfig(),
    )


class _DummySession:  # pragma: no cover - trivial test double
    """Lightweight stand-in for SQLModel Session."""


class _DummyService:  # pragma: no cover - trivial test double
    """Simple stand-in for ItemSalvageService."""


def _override_session() -> Generator[object, None, None]:
    dummy_session = _DummySession()
    yield dummy_session


def _override_service() -> object:
    return _DummyService()


def test_health_endpoint(request: pytest.FixtureRequest) -> None:
    """Test /health endpoint returns status ok and app_name from config."""
    config = request.getfixturevalue("test_config")
    app = create_app()
    app.dependency_overrides[get_config] = lambda: config
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "TestApp"


def test_sample_endpoint(request: pytest.FixtureRequest) -> None:
    """Test /sample endpoint returns correct DI types and config value."""
    config = request.getfixturevalue("test_config")
    app = create_app()
    app.dependency_overrides[get_config] = lambda: config
    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_service] = _override_service
    client = TestClient(app)
    response = client.get("/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "TestApp"
    assert data["db_type"] == _DummySession.__name__
    assert data["service_type"] == _DummyService.__name__
