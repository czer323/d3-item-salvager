from types import SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def test_base_includes_backend_base_meta(
    frontend_app: "Flask", frontend_config: SimpleNamespace
) -> None:
    # Use the canonical `frontend_config` fixture so tests share the same defaults
    with frontend_app.test_request_context("/"):
        html = frontend_app.jinja_env.get_template("layout/base.html").render(
            frontend_config=frontend_config
        )
    assert (
        f'<meta name="backend-base" content="{frontend_config.backend_base_url}"'
        in html
    )
