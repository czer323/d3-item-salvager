"""Frontend application entrypoint for the d3-item-salvager UI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from flask import Flask, g

from frontend.src.config import FrontendConfig
from frontend.src.routes import register_blueprints
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

    # Template filter: sanitize item names to hide internal ids like P4_Unique_*
    def sanitize_item_name(value: object | None) -> str:
        import re

        if value is None:
            return ""
        s = str(value).strip()
        # Remove leading internal tokens like P4_ or P66_
        s = re.sub(r"\bP\d+_", "", s)
        # Remove 'Unique_' tokens
        s = re.sub(r"\bUnique_", "", s, flags=re.IGNORECASE)
        # Replace underscores with spaces and collapse whitespace
        s = s.replace("_", " ")
        s = " ".join(s.split())
        return s or str(value)

    app.jinja_env.filters["sanitize_item_name"] = sanitize_item_name

    register_blueprints(app)
    return app
