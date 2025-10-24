"""Utilities for serialising and validating user selection preferences."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from frontend.src.services.selection import SelectionViewModel

PREFERENCES_VERSION = 1
PREFERENCES_STORAGE_KEY = "d3-item-salvager.preferences"


class PreferencesValidationError(ValueError):
    """Raised when a stored preferences payload cannot be validated."""


@dataclass(frozen=True, slots=True)
class PreferencesState:
    """Immutable representation of a user preference snapshot."""

    version: int
    classes: tuple[str, ...]
    builds: tuple[str, ...]
    variants: tuple[str, ...]


def compose_preferences(
    selection_view: SelectionViewModel | None,
    *,
    default_variant_ids: Sequence[str],
) -> PreferencesState:
    """Create a snapshot of the current selections for local persistence.

    Args:
        selection_view: The current selection view rendered for the request.
        default_variant_ids: Variant identifiers used when no variant selection
            is available in the view.

    Returns:
        A :class:`PreferencesState` capturing the selection and version.
    """
    classes = _collect_selected_ids(
        selection_view.classes if selection_view else (),
        extra=(selection_view.selected_class_id,) if selection_view else (),
    )
    builds = _collect_selected_ids(
        selection_view.builds if selection_view else (),
        extra=(selection_view.selected_build_id,) if selection_view else (),
    )
    variants = _collect_selected_ids(
        selection_view.variants if selection_view else (),
        extra=(selection_view.selected_variant_id,) if selection_view else (),
    )

    if not variants:
        variants = _normalize_iterable(default_variant_ids)

    return PreferencesState(
        version=PREFERENCES_VERSION,
        classes=classes,
        builds=builds,
        variants=variants,
    )


def to_payload(state: PreferencesState) -> dict[str, Any]:
    """Convert a preference snapshot into a JSON-serialisable dictionary."""
    return {
        "version": state.version,
        "classes": list(state.classes),
        "builds": list(state.builds),
        "variants": list(state.variants),
    }


def export_preferences(state: PreferencesState) -> str:
    """Serialise a preference snapshot into a compact JSON string."""
    return json.dumps(
        to_payload(state),
        sort_keys=True,
        separators=(",", ":"),
    )


def import_preferences(payload: object) -> PreferencesState:
    """Parse stored preferences from JSON or mapping form.

    Args:
        payload: A JSON string, mapping or :class:`PreferencesState` instance
            describing previously-saved preferences.

    Returns:
        A validated :class:`PreferencesState` instance.

    Raises:
        PreferencesValidationError: When the payload cannot be parsed or does
            not match the expected schema/version.
    """
    if isinstance(payload, PreferencesState):
        return payload

    decoded: Mapping[str, Any]
    if isinstance(payload, (bytes, bytearray)):
        payload = payload.decode("utf-8")

    if isinstance(payload, str):
        try:
            raw = json.loads(payload)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
            msg = "Preferences JSON could not be decoded"
            raise PreferencesValidationError(msg) from exc
        if not isinstance(raw, Mapping):
            msg = "Preferences JSON must decode to an object"
            raise PreferencesValidationError(msg)
        decoded = cast("Mapping[str, Any]", raw)
    elif isinstance(payload, Mapping):
        decoded = cast("Mapping[str, Any]", payload)
    else:  # pragma: no cover - defensive guard
        msg = f"Unsupported preferences payload type: {type(payload)!r}"
        raise PreferencesValidationError(msg)

    return _coerce_state(decoded)


def _coerce_state(data: Mapping[str, Any]) -> PreferencesState:
    version = data.get("version")
    if version != PREFERENCES_VERSION:
        msg = "Preferences payload version mismatch"
        raise PreferencesValidationError(msg)

    classes = _normalize_iterable(_as_iterable(data.get("classes", ()), "classes"))
    builds = _normalize_iterable(_as_iterable(data.get("builds", ()), "builds"))
    variants = _normalize_iterable(_as_iterable(data.get("variants", ()), "variants"))

    return PreferencesState(
        version=PREFERENCES_VERSION,
        classes=classes,
        builds=builds,
        variants=variants,
    )


def _collect_selected_ids(
    options: Iterable[object],
    *,
    extra: Iterable[str | None] = (),
) -> tuple[str, ...]:
    values: list[str | None] = [
        getattr(option, "id", None)
        for option in options
        if getattr(option, "selected", False)
    ]
    values.extend(extra)
    return _normalize_iterable(values)


def _normalize_iterable(values: Iterable[object]) -> tuple[str, ...]:
    normalised: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        if text not in seen:
            seen.add(text)
            normalised.append(text)
    return tuple(normalised)


def _as_iterable(value: object, field_name: str) -> Iterable[object]:
    if isinstance(value, (str, bytes, bytearray)):
        msg = f"Preferences field '{field_name}' must be an iterable"
        raise PreferencesValidationError(msg)
    if not isinstance(value, Iterable):
        msg = f"Preferences field '{field_name}' must be an iterable"
        raise PreferencesValidationError(msg)
    return cast("Iterable[object]", value)


__all__ = [
    "PREFERENCES_STORAGE_KEY",
    "PREFERENCES_VERSION",
    "PreferencesState",
    "PreferencesValidationError",
    "compose_preferences",
    "export_preferences",
    "import_preferences",
    "to_payload",
]
