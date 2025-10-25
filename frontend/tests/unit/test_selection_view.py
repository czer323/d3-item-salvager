"""Unit tests for the selection service view model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping

    from frontend.src.services.backend_client import BackendClient


@dataclass(slots=True)
class _Request:
    path: str


class FakeBackendClient:
    """Simple backend client stub returning registered payloads."""

    def __init__(self, responses: dict[str, object]) -> None:
        self._responses = responses
        self.requests: list[_Request] = []

    def get_json(
        self, path: str, *, params: Mapping[str, object] | None = None
    ) -> object:
        _ = params
        self.requests.append(_Request(path=path))
        try:
            return self._responses[path]
        except KeyError as exc:  # pragma: no cover - guard for unexpected paths
            msg = f"Unexpected backend path requested: {path}"
            raise AssertionError(msg) from exc


@pytest.fixture(name="fake_client")
def fake_client_fixture() -> FakeBackendClient:
    """Provide a backend client preloaded with selection data fixtures."""
    responses: dict[str, object] = {
        "/build-guides": [
            {"id": 1, "title": "Barb Slam", "class_name": "Barbarian"},
            {"id": 2, "title": "Arcane Orb", "class_name": "Wizard"},
            {"id": 3, "title": "Leap Quake", "class_name": "Barbarian"},
        ],
        "/build-guides/1/variants": [
            {"id": "v-barb-1", "name": "Raekor Slam", "build_guide_id": 1},
            {"id": "v-barb-2", "name": "HotA Slam", "build_guide_id": 1},
        ],
        "/build-guides/2/variants": [],
        "/builds/2/variants": [],
        "/variants/2": [],
        "/build-guides/3/variants": [
            {"id": "v-barb-3", "name": "Leap Quake", "build_guide_id": 3},
        ],
        "/variants/v-barb-1": {
            "id": "v-barb-1",
            "name": "Raekor Slam",
            "build_guide_id": 1,
        },
        "/variants/v-barb-3": {
            "id": "v-barb-3",
            "name": "Leap Quake",
            "build_guide_id": 3,
        },
    }
    return FakeBackendClient(responses)


def test_build_selection_view_groups_builds_by_class_and_marks_selected(
    fake_client: FakeBackendClient,
) -> None:
    """Default selection should honour variant defaults and mark active options."""
    from frontend.src.services.selection import build_selection_view

    view = build_selection_view(
        cast("BackendClient", fake_client),
    )

    expected_classes = {
        "Barbarian",
        "Crusader",
        "Demon Hunter",
        "Monk",
        "Necromancer",
        "Witch Doctor",
        "Wizard",
    }
    assert set(view.selected_class_ids) == expected_classes
    assert tuple(sorted(view.selected_build_ids)) == ("1", "2", "3")
    assert view.selected_variant_ids == ()

    class_labels = {option.label for option in view.classes}
    assert class_labels == expected_classes
    for class_option in view.classes:
        # All classes are active when no explicit selection is provided.
        assert class_option.selected is True
    barbarian_option = next(
        option for option in view.classes if option.id == "Barbarian"
    )
    assert barbarian_option.build_count == 2

    # Only builds for the selected class should be surfaced in the build dropdown.
    build_ids = [option.id for option in view.builds]
    assert build_ids == ["1", "3", "2"]
    selected_build_ids = {option.id for option in view.builds if option.selected}
    assert selected_build_ids == {"1", "2", "3"}

    assert view.variants == ()

    # Ensure the backend was queried for builds only (variants are deferred to item lookup).
    requested_paths = {request.path for request in fake_client.requests}
    assert "/build-guides" in requested_paths
    assert not any(path.endswith("/variants") for path in requested_paths)


def test_build_selection_view_skips_build_loading_until_requested() -> None:
    """Classes are returned without build data when load_builds is disabled."""
    from frontend.src.services.selection import build_selection_view

    view = build_selection_view(
        client=cast("BackendClient", FakeBackendClient({})),
        load_builds=False,
    )

    assert view.builds == ()
    assert view.variants == ()
    class_names = {option.id for option in view.classes}
    expected_classes = {
        "Barbarian",
        "Crusader",
        "Demon Hunter",
        "Monk",
        "Necromancer",
        "Witch Doctor",
        "Wizard",
    }
    assert class_names == expected_classes


def test_build_selection_view_respects_explicit_selection(
    fake_client: FakeBackendClient,
) -> None:
    """Explicit class/build/variant arguments should override defaults."""
    from frontend.src.services.selection import build_selection_view

    view = build_selection_view(
        cast("BackendClient", fake_client),
        class_ids=("Wizard",),
        build_ids=("2",),
    )

    # No variants are registered for the wizard build in the fake client, so the
    # service should gracefully fall back to an empty collection while retaining
    # the explicit selections.
    assert view.selected_class_ids == ("Wizard",)
    assert view.selected_build_ids == ("2",)
    assert view.selected_variant_ids == ()
    assert view.variants == ()
