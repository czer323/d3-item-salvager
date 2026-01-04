"""Failing unit tests for the builds service wiring (T011a).

These tests assert that the client-side service file `frontend/src/services/builds.js`
exists and exposes a `fetchBuildItems` export. They will fail until the file is
created and the expected function is present.
"""

from __future__ import annotations

from pathlib import Path


def test_builds_service_file_exists() -> None:
    path = Path(__file__).resolve().parents[2] / "src" / "services" / "builds.js"
    assert path.exists(), f"Expected builds service at {path}"


def test_builds_service_exports_fetch_function() -> None:
    path = Path(__file__).resolve().parents[2] / "src" / "services" / "builds.js"
    content = path.read_text() if path.exists() else ""
    assert "fetchBuildItems" in content, (
        "Expected 'fetchBuildItems' to be defined in frontend src/services/builds.js"
    )
