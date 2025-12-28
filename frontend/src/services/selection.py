"""Selection data access helpers for the dashboard controls."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from frontend.src.services.backend_catalog import (
    BuildRecord,
    normalise_id_iterable,
)
from frontend.src.services.backend_catalog import (
    load_builds as fetch_build_records,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from frontend.src.services.backend_client import BackendClient

CLASS_CATALOGUE: tuple[str, ...] = (
    "Barbarian",
    "Crusader",
    "Demon Hunter",
    "Monk",
    "Necromancer",
    "Witch Doctor",
    "Wizard",
)


@dataclass(frozen=True, slots=True)
class ClassOption:
    """Selectable representation of a character class."""

    id: str
    label: str
    build_count: int
    selected: bool


@dataclass(frozen=True, slots=True)
class BuildOption:
    """Selectable representation of a build guide."""

    id: str
    label: str
    class_id: str
    selected: bool


@dataclass(frozen=True, slots=True)
class VariantOption:
    """Selectable representation of a build variant."""

    id: str
    label: str
    build_id: str
    selected: bool


@dataclass(frozen=True, slots=True)
class SelectionViewModel:
    """Aggregated options used to render the selection controls."""

    classes: tuple[ClassOption, ...]
    builds: tuple[BuildOption, ...]
    variants: tuple[VariantOption, ...]
    selected_class_ids: tuple[str, ...]
    selected_build_ids: tuple[str, ...]
    selected_variant_ids: tuple[str, ...]

    @property
    def has_variants(self) -> bool:
        """Return True when variant options are available."""
        return bool(self.variants)

    @property
    def selected_variant_count(self) -> int:
        """Return how many variants are currently active."""
        return len(self.selected_variant_ids)


def build_selection_view(
    client: BackendClient,
    *,
    class_ids: Sequence[str] | None = None,
    build_ids: Sequence[str] | None = None,
    load_builds: bool = True,
) -> SelectionViewModel:
    """Compose selection controls for the dashboard views."""
    requested_class_ids = normalise_id_iterable(class_ids)
    requested_build_ids = normalise_id_iterable(build_ids)

    if not load_builds:
        class_options = _build_class_options(requested_class_ids)
        return SelectionViewModel(
            classes=class_options,
            builds=(),
            variants=(),
            selected_class_ids=tuple(
                option.id for option in class_options if option.selected
            ),
            selected_build_ids=(),
            selected_variant_ids=(),
        )

    builds = fetch_build_records(client)

    if not builds:
        return SelectionViewModel(
            classes=(),
            builds=(),
            variants=(),
            selected_class_ids=requested_class_ids,
            selected_build_ids=requested_build_ids,
            selected_variant_ids=(),
        )

    class_groups: dict[str, list[BuildRecord]] = defaultdict(list)
    for record in builds:
        class_groups[record.class_name].append(record)

    referenced_classes = {*class_groups.keys(), *CLASS_CATALOGUE}
    sorted_classes = tuple(sorted(referenced_classes, key=str.casefold))
    all_class_ids = tuple(sorted_classes)

    if requested_class_ids:
        # Respect explicit selections but only include those classes that have matching builds.
        # Do NOT fallback to all classes if the requested classes are missing; this avoids
        # unintentionally showing every build when a user selects a class with no available builds.
        active_class_ids = tuple(
            class_id for class_id in requested_class_ids if class_id in class_groups
        )
    else:
        active_class_ids = all_class_ids

    # Mark classes as selected based on explicit requested_class_ids when provided;
    # otherwise, default to selecting all classes.
    if requested_class_ids:
        selected_set = set(requested_class_ids)
    else:
        selected_set = set(all_class_ids)

    class_options = tuple(
        ClassOption(
            id=class_name,
            label=class_name,
            build_count=len(class_groups.get(class_name, [])),
            selected=class_name in selected_set,
        )
        for class_name in sorted_classes
    )

    # Determine the build records that should be surfaced based on class selection.
    active_build_records: list[BuildRecord] = []
    for class_id in active_class_ids:
        active_build_records.extend(class_groups.get(class_id, []))

    ordered_build_ids = tuple(record.id for record in active_build_records)
    available_build_ids = set(ordered_build_ids)

    if requested_build_ids:
        active_build_ids = tuple(
            build_id
            for build_id in requested_build_ids
            if build_id in available_build_ids
        )
        if not active_build_ids:
            active_build_ids = ordered_build_ids
    else:
        active_build_ids = ordered_build_ids

    selected_build_id_set = set(active_build_ids)
    build_option_list = [
        BuildOption(
            id=record.id,
            label=record.title,
            class_id=record.class_name,
            selected=record.id in selected_build_id_set,
        )
        for record in builds
    ]

    resolved_variant_options: tuple[VariantOption, ...] = ()
    active_variant_ids: tuple[str, ...] = ()

    filtered_build_options = tuple(
        option
        for option in build_option_list
        if option.class_id in active_class_ids or option.selected
    )

    return SelectionViewModel(
        classes=class_options,
        builds=filtered_build_options,
        variants=resolved_variant_options,
        selected_class_ids=tuple(
            option.id for option in class_options if option.selected
        ),
        selected_build_ids=tuple(build_id for build_id in active_build_ids),
        selected_variant_ids=active_variant_ids,
    )


def _build_class_options(selected_ids: Sequence[str]) -> tuple[ClassOption, ...]:
    selected_set: set[str] = set(selected_ids)
    return tuple(
        ClassOption(
            id=class_name,
            label=class_name,
            build_count=0,
            selected=class_name in selected_set,
        )
        for class_name in CLASS_CATALOGUE
    )
