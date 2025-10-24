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
from frontend.src.services.selection import (
    BuildOption,
    ClassOption,
    SelectionViewModel,
    VariantOption,
)


def _build_selection_view(
    *,
    class_id: str,
    build_id: str,
    variant_id: str,
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
        variants=(
            VariantOption(
                id=variant_id,
                label=f"Variant {variant_id}",
                build_id=build_id,
                selected=True,
            ),
        ),
        selected_class_id=class_id,
        selected_build_id=build_id,
        selected_variant_id=variant_id,
    )


def test_compose_preferences_reflects_active_selection() -> None:
    """Selected class/build/variant identifiers are captured in the snapshot."""
    selection_view = _build_selection_view(
        class_id="barbarian",
        build_id="build-1",
        variant_id="variant-7",
    )

    state = compose_preferences(
        selection_view,
        default_variant_ids=("fallback",),
    )

    assert state.version == PREFERENCES_VERSION
    assert state.classes == ("barbarian",)
    assert state.builds == ("build-1",)
    assert state.variants == ("variant-7",)


def test_compose_preferences_uses_default_variants_when_selection_missing() -> None:
    """Default variant identifiers populate the snapshot when selection is absent."""
    state = compose_preferences(None, default_variant_ids=("demo-alpha", "demo-beta"))

    assert state.classes == ()
    assert state.builds == ()
    assert state.variants == ("demo-alpha", "demo-beta")


def test_import_preferences_round_trips_serialized_payload() -> None:
    """Exported JSON payloads can be imported without data loss."""
    selection_view = _build_selection_view(
        class_id="wizard",
        build_id="build-9",
        variant_id="variant-2",
    )
    original_state = compose_preferences(selection_view, default_variant_ids=())

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
            "variants": [],
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
            "variants": [],
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
        variants=(),
    )

    exported = export_preferences(empty_state)
    decoded = json.loads(exported)

    assert decoded == {
        "version": PREFERENCES_VERSION,
        "classes": [],
        "builds": [],
        "variants": [],
    }
