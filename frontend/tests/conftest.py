"""Pytest fixtures for frontend UI and contract tests."""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Iterator
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest
from werkzeug.serving import make_server

from frontend.app import create_app

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flask import Flask
    from werkzeug.test import Client as FlaskClient


_SERVER_READY_POLL_SECONDS = 0.05
_SERVER_READY_TIMEOUT_SECONDS = 2.0


def _wait_for_server(port: int) -> None:
    """Poll until the development server is ready to accept connections."""
    deadline = time.perf_counter() + _SERVER_READY_TIMEOUT_SECONDS
    while time.perf_counter() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return
        except OSError:
            time.sleep(_SERVER_READY_POLL_SECONDS)
    msg = "Frontend server did not start before timeout"
    raise RuntimeError(msg)


@pytest.fixture(scope="session")
def frontend_app() -> Flask:
    """Create the Flask application once per test session."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="session")
def frontend_server_url(frontend_app: Flask) -> Iterator[str]:
    """Run the Flask app on an ephemeral port for Playwright and API tests."""
    server = make_server("127.0.0.1", 0, frontend_app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _wait_for_server(port)

    base_url = f"http://127.0.0.1:{port}"
    os.environ["FRONTEND_BASE_URL"] = base_url
    os.environ["FRONTEND_PLAYWRIGHT_PORT"] = str(port)

    try:
        yield base_url
    finally:
        server.shutdown()
        thread.join(timeout=5)
        if thread.is_alive():
            msg = "Frontend server thread did not terminate within timeout"
            raise RuntimeError(msg)


@pytest.fixture
def client(frontend_app: Flask) -> Iterator[FlaskClient]:
    """Provide a Flask test client for API-level assertions."""
    with frontend_app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Additional fixtures to centralize test data and common test behaviour
# ---------------------------------------------------------------------------
from frontend.src.services.backend_catalog import ItemRecord
from frontend.src.services.backend_client import BackendClient


@pytest.fixture(scope="session")
def frontend_config() -> SimpleNamespace:
    """Canonical frontend config object available to tests.

    Mirrors the shape of `FrontendConfig` with the attributes used in templates
    (e.g. `backend_base_url`). Defaults to `FRONTEND_BASE_URL` if set by the
    test server helper; otherwise falls back to localhost.
    """
    base = os.environ.get("FRONTEND_BASE_URL", "http://127.0.0.1")
    return SimpleNamespace(backend_base_url=base, request_timeout_seconds=10.0)


@pytest.fixture
def with_frontend_config(
    client: FlaskClient, frontend_config: SimpleNamespace
) -> Iterator[None]:
    """Temporarily set `FRONTEND_CONFIG` in `app.config` for the duration of a test."""
    app = cast("Flask", client.application)
    if "FRONTEND_CONFIG" in app.config:
        orig: object = cast("object", app.config["FRONTEND_CONFIG"])
        # restore the original after the test
        had = True
    else:
        orig = None
        had = False

    app.config["FRONTEND_CONFIG"] = frontend_config
    try:
        yield
    finally:
        # restore the prior state (either delete or set the original value)
        if had:
            app.config["FRONTEND_CONFIG"] = orig
        else:
            del app.config["FRONTEND_CONFIG"]


@pytest.fixture
def sample_catalogue() -> list[ItemRecord]:
    """Small sample item catalogue used across frontend tests."""
    return [
        ItemRecord(id="a", name="alpha", slot="Weapon"),
        ItemRecord(id="b", name="Alpha", slot="Weapon"),
        ItemRecord(id="c", name="beta", slot="Offhand"),
    ]


@pytest.fixture
def sample_usage_map() -> dict[str, object]:
    """Sample usage accumulator mapping used by item usage tests."""
    return {
        "a": SimpleNamespace(
            name="alpha", slot="Weapon", contexts=set(), variant_ids=set()
        ),
        "b": SimpleNamespace(
            name="Alpha", slot="Weapon", contexts=set(), variant_ids=set()
        ),
        "c": SimpleNamespace(
            name="beta", slot="Offhand", contexts=set(), variant_ids=set()
        ),
    }


@pytest.fixture
def patched_item_usage_loaders(
    monkeypatch: pytest.MonkeyPatch,
    sample_catalogue: list[ItemRecord],
    sample_usage_map: dict[str, object],
) -> None:
    """Monkeypatch the catalogue loader and usage collector with sane test data."""

    def _load_catalogue(_client: object) -> list[ItemRecord]:
        return sample_catalogue

    def _collect_usage(_client: object, _ids: list[str]) -> dict[str, object]:
        return sample_usage_map

    monkeypatch.setattr(
        "frontend.src.services.item_usage.load_item_catalogue",
        _load_catalogue,
    )
    monkeypatch.setattr(
        "frontend.src.services.item_usage._collect_usage_for_builds",
        _collect_usage,
    )


@pytest.fixture
def patched_build_usage_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """Monkeypatch the items route build function to return a small fake table."""

    def _fake_table(_client: object, _source: object) -> SimpleNamespace:
        """Return a minimal SimpleNamespace table used by route tests."""
        return SimpleNamespace(
            total_items=1,
            used_total=1,
            filters=SimpleNamespace(search="", slot=""),
            pagination=SimpleNamespace(page_size=50),
            rows=[
                SimpleNamespace(
                    item_id="item-1",
                    name="Mighty Weapon",
                    slot="Weapon",
                    badge_class="badge-success",
                    is_used=True,
                    usage_label="main",
                    variant_ids=(1,),
                )
            ],
        )

    monkeypatch.setattr("frontend.src.routes.items._build_usage_table", _fake_table)
    monkeypatch.setattr(
        "frontend.src.routes.items._get_backend_client", lambda: object()
    )


@pytest.fixture
def no_frontend_config(client: FlaskClient) -> Iterator[None]:
    """Ensure `FRONTEND_CONFIG` is absent for the duration of a test."""
    app = cast("Flask", client.application)

    if "FRONTEND_CONFIG" in app.config:
        orig: object = cast("object", app.config["FRONTEND_CONFIG"])
        del app.config["FRONTEND_CONFIG"]
    else:
        orig = None

    try:
        yield
    finally:
        if orig is not None:
            app.config["FRONTEND_CONFIG"] = orig


@pytest.fixture
def backend_client() -> Iterator[BackendClient]:
    """A lightweight BackendClient for tests. Network calls should be stubbed by tests/fixtures."""
    client = BackendClient(
        base_url=os.environ.get("FRONTEND_BASE_URL", "http://127.0.0.1"),
        timeout_seconds=0.1,
    )
    try:
        yield client
    finally:
        client.close()
