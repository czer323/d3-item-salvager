"""Unit test for FastAPI /health endpoint in factory.py."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from d3_item_salvager.api.dependencies import get_config
from d3_item_salvager.api.factory import create_app
from d3_item_salvager.config.base import (
    DatabaseConfig,
    LoggingConfig,
    MaxrollParserConfig,
)
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.container import Container


@pytest.fixture(autouse=True)
def reset_container_config() -> Generator[None, None, None]:
    """Reset DI container config override after each test."""
    yield
    Container.config.reset_override()


@pytest.fixture
def test_config() -> AppConfig:
    """Fixture for DummyConfig used in dependency overrides."""
    return AppConfig(
        app_name="TestApp",
        database=DatabaseConfig(url="sqlite:///:memory:"),
        maxroll_parser=MaxrollParserConfig(bearer_token="dummy-token"),
        logging=LoggingConfig(),
    )


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
    # Patch DI container config provider
    Container.config.override(config)
    app = create_app()
    app.dependency_overrides[get_config] = lambda: config
    client = TestClient(app)
    response = client.get("/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "TestApp"
    assert data["db_type"] == "Session"
    assert data["service_type"] == "ItemSalvageService"
