"""Frontend application entrypoint for the d3-item-salvager UI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from flask import Flask, g

from frontend.src.config import FrontendConfig
from frontend.src.services.backend_client import BackendClient

if TYPE_CHECKING:
    from collections.abc import Callable


def _configure_logging(debug_enabled: bool) -> None:
    """Configure logging level based on the debug flag."""
    target_level = logging.DEBUG if debug_enabled else logging.INFO
    logging.basicConfig(level=target_level)


def _create_backend_client_factory(
    config: FrontendConfig,
) -> Callable[[], BackendClient]:
    """Return a factory callable that produces configured backend clients."""

    def _factory() -> BackendClient:
        return BackendClient(
            base_url=config.backend_base_url,
            timeout_seconds=config.request_timeout_seconds,
        )

    return _factory


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    load_dotenv()
    config = FrontendConfig.from_env()
    _configure_logging(config.debug)

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["FRONTEND_CONFIG"] = config
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    app.url_map.strict_slashes = False

    backend_client_factory = _create_backend_client_factory(config)

    def _inject_client() -> None:
        g.backend_client = backend_client_factory()

    def _teardown_client(_: object) -> None:
        client = getattr(g, "backend_client", None)
        if client is not None:
            client.close()

    app.before_request(_inject_client)
    app.teardown_request(_teardown_client)

    from frontend.src.routes import base_blueprint

    app.register_blueprint(base_blueprint)
    return app
