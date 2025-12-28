"""Integration test ensuring frontend and backend interoperate via real HTTP calls."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from d3_item_salvager.api.dependencies import get_db_session
from d3_item_salvager.api.factory import create_app as create_backend_app
from frontend import app as frontend_app_module
from frontend.src.services.backend_client import BackendClient
from tests.fakes.test_db_utils import seed_salvage_dataset

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine
else:  # pragma: no cover - typing fallbacks for runtime
    Generator = Any  # type: ignore[assignment]
    Engine = Any  # type: ignore[assignment]


@pytest.mark.usefixtures("sqlite_test_engine")
def test_frontend_variant_json_round_trip(
    sqlite_test_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Frontend JSON endpoint should reflect live backend data."""
    engine = sqlite_test_engine
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        dataset = seed_salvage_dataset(session)

    backend_app = create_backend_app()

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    backend_app.dependency_overrides[get_db_session] = override_session

    backend_http_client = TestClient(backend_app)

    def _mock_handler(request: httpx.Request) -> httpx.Response:
        target = request.url.path
        if request.url.query:
            target = f"{target}?{request.url.query}"
        response = backend_http_client.request(
            request.method,
            target,
            headers=request.headers,
            content=request.content,
        )
        return httpx.Response(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
        )

    client_transport = httpx.MockTransport(_mock_handler)

    monkeypatch.setenv("FRONTEND_BACKEND_URL", "http://testserver")

    def custom_factory(config: frontend_app_module.FrontendConfig) -> object:
        def _factory() -> BackendClient:
            return BackendClient(
                base_url=config.backend_base_url,
                timeout_seconds=config.request_timeout_seconds,
                transport=client_transport,
            )

        return _factory

    monkeypatch.setattr(
        frontend_app_module,
        "_create_backend_client_factory",
        custom_factory,
    )

    flask_app = frontend_app_module.create_app()
    test_client = flask_app.test_client()

    build_id = dataset["builds"]["one"]
    response = test_client.get(
        "/frontend/items/summary.json",
        query_string={"build_ids": build_id},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["filters"]["search"] == ""
    assert str(build_id) in payload["context"]["build_ids"]
    item_ids = {entry["item_id"] for entry in payload["rows"]}
    assert dataset["items"]["weapon"] in item_ids
    used_entries = [entry for entry in payload["rows"] if entry["status"] == "used"]
    assert any(entry["name"] == "Mighty Weapon" for entry in used_entries)

    # Now test that requesting a class with no builds results in an empty build list
    post_resp = test_client.post(
        "/frontend/selection/controls",
        data={"action": "load_builds", "class_ids": "Monk"},
    )
    assert post_resp.status_code == 200
    html = post_resp.get_data(as_text=True)
    # The builds select should be present but have no <option> entries for builds
    assert 'name="build_ids"' in html
    # Ensure the specific builds select block contains no <option> entries
    start = html.find('name="build_ids"')
    select_start = html.rfind("<select", 0, start)
    select_end = html.find("</select>", start)
    assert select_start != -1, "Could not locate the start of the builds select element"
    assert select_end != -1, "Could not locate the end of the builds select element"
    builds_block = html[select_start:select_end]
    assert "<option" not in builds_block

    backend_app.dependency_overrides.clear()
    backend_http_client.close()
