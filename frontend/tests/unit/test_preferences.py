"""Unit tests for the frontend preferences service."""

from __future__ import annotations

import json

import pytest

from frontend.src.services.preferences import (
    PREFERENCES_VERSION,
    PreferencesState,
    PreferencesValidationError,
    compose_preferences,
    export_preferences,
    import_preferences,
)
from frontend.src.services.selection import BuildOption, ClassOption, SelectionViewModel


def _build_selection_view(
    *,
    class_id: str,
    build_id: str,
) -> SelectionViewModel:
    """Construct a minimal selection view populated with chosen options."""
    return SelectionViewModel(
        classes=(
            ClassOption(
                id=class_id,
                label=class_id.title(),
                build_count=1,
                selected=True,
            ),
        ),
        builds=(
            BuildOption(
                id=build_id,
                label=f"Build {build_id}",
                class_id=class_id,
                selected=True,
            ),
        ),
        variants=(),
        selected_class_ids=(class_id,),
        selected_build_ids=(build_id,),
        selected_variant_ids=(),
    )


def test_compose_preferences_reflects_active_selection() -> None:
    """Selected class/build identifiers are captured in the snapshot."""
    selection_view = _build_selection_view(
        class_id="barbarian",
        build_id="build-1",
    )

    state = compose_preferences(selection_view)

    assert state.version == PREFERENCES_VERSION
    assert state.classes == ("barbarian",)
    assert state.builds == ("build-1",)


def test_compose_preferences_returns_empty_state_when_selection_missing() -> None:
    """Missing selections produce an empty snapshot."""
    state = compose_preferences(None)

    assert state.classes == ()
    assert state.builds == ()


def test_import_preferences_round_trips_serialized_payload() -> None:
    """Exported JSON payloads can be imported without data loss."""
    selection_view = _build_selection_view(
        class_id="wizard",
        build_id="build-9",
    )
    original_state = compose_preferences(selection_view)

    exported = export_preferences(original_state)
    imported_state = import_preferences(exported)

    assert imported_state == original_state


def test_import_preferences_rejects_mismatched_version() -> None:
    """Preferences payloads with an unexpected version are rejected."""
    payload = json.dumps(
        {
            "version": PREFERENCES_VERSION + 1,
            "classes": ["wizard"],
            "builds": [],
        }
    )

    with pytest.raises(PreferencesValidationError):
        import_preferences(payload)


def test_import_preferences_requires_iterable_fields() -> None:
    """Non-iterable fields raise validation errors during import."""
    payload = json.dumps(
        {
            "version": PREFERENCES_VERSION,
            "classes": "druid",
            "builds": [],
        }
    )

    with pytest.raises(PreferencesValidationError):
        import_preferences(payload)


def test_export_preferences_normalises_empty_collections() -> None:
    """Empty preference snapshots serialise to arrays in the JSON payload."""
    empty_state = PreferencesState(
        version=PREFERENCES_VERSION,
        classes=(),
        builds=(),
    )

    exported = export_preferences(empty_state)
    decoded = json.loads(exported)

    assert decoded == {
        "version": PREFERENCES_VERSION,
        "classes": [],
        "builds": [],
    }


def test_import_preferences_upgrades_version_one_payloads() -> None:
    """Legacy version 1 payloads are coerced into the new schema."""
    payload = json.dumps(
        {
            "version": 1,
            "classes": ["barbarian"],
            "builds": ["build-1"],
            "variants": ["legacy"],
        }
    )

    state = import_preferences(payload)

    assert state.classes == ("barbarian",)
    assert state.builds == ("build-1",)
