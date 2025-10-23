"""Pytest fixtures for frontend UI and contract tests."""

from __future__ import annotations

import os
import socket
import threading
import time
from typing import TYPE_CHECKING

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
    os.environ.setdefault("FRONTEND_BASE_URL", base_url)
    os.environ.setdefault("FRONTEND_PLAYWRIGHT_PORT", str(port))

    try:
        yield base_url
    finally:
        server.shutdown()
        thread.join(timeout=5)


@pytest.fixture
def client(frontend_app: Flask) -> Iterator[FlaskClient]:
    """Provide a Flask test client for API-level assertions."""
    with frontend_app.test_client() as test_client:
        yield test_client
