"""Search utilities for backend (ported from frontend canonical implementation).

Contains fuzzy_score, FilterCriteria, apply_filters and pagination helpers used by
search and lookup endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence
else:  # pragma: no cover - runtime fallback for typing helpers
    import collections.abc as _abc

    Sequence = _abc.Sequence


class SupportsFiltering(Protocol):
    """Protocol describing the fields required for filtering operations."""

    name: str
    slot: str


@dataclass(frozen=True, slots=True)
class FilterCriteria:
    """Criteria applied when filtering variant summary items."""

    search: str = ""
    slot: str | None = None

    @property
    def search_term(self) -> str:
        """Return a normalised search term for comparisons."""
        return _normalise_token(self.search)

    @property
    def slot_value(self) -> str | None:
        """Return a normalised slot identifier when one is configured."""
        if self.slot is None:
            return None
        value = self.slot.strip()
        return value.casefold() or None

    def is_empty(self) -> bool:
        """Return True when no search or slot criteria are set."""
        return not self.search_term and self.slot_value is None


def fuzzy_score(candidate: str, query: str) -> int:
    """Return a basic fuzzy match score between the candidate and query.

    The scoring favours prefix and substring matches while still granting a
    positive score for subsequence matches (characters in order with gaps).
    Non-matching candidates return zero.
    """
    candidate_token = _normalise_token(candidate)
    query_token = _normalise_token(query)
    if not query_token:
        return 100
    if not candidate_token:
        return 0

    if candidate_token.startswith(query_token):
        # Strong prefix match — higher score for longer matches.
        return 90 + min(len(query_token), 10)
    if query_token in candidate_token:
        # Substring matches rank slightly below prefixes.
        position = candidate_token.find(query_token)
        return 75 + max(0, 10 - position)

    # Subsequence comparison: iterate through candidate characters, rewarding
    # in-order matches while penalising large gaps between characters.
    match_index = 0
    gap_penalty = 0
    for char in candidate_token:
        if match_index >= len(query_token):
            break
        if char == query_token[match_index]:
            match_index += 1
        elif match_index > 0:
            gap_penalty += 1
    if match_index == len(query_token):
        return max(30, 60 - gap_penalty)
    return 0


def apply_filters[TFiltered: SupportsFiltering](
    items: Sequence[TFiltered],
    criteria: FilterCriteria,
) -> list[TFiltered]:
    """Return items matching the provided filter criteria."""
    if criteria.is_empty():
        return list(items)

    slot_value = criteria.slot_value
    search_term = criteria.search_term

    filtered: list[TFiltered] = []
    for item in items:
        if slot_value is not None and item.slot.casefold() != slot_value:
            continue
        if not search_term:
            filtered.append(item)
            continue
        score = fuzzy_score(item.name, search_term)
        if score > 0:
            filtered.append(item)
    return filtered


def _normalise_token(value: str | None) -> str:
    if not value:
        return ""
    return "".join(char for char in value.casefold() if char.isalnum())


# Public alias for external modules that need token normalisation.
# This keeps the original implementation private but exposes a supported
# public API to avoid importing module-private names from other packages.
def normalise_token(value: str | None) -> str:
    return _normalise_token(value)


__all__ = [
    "FilterCriteria",
    "SupportsFiltering",
    "apply_filters",
    "fuzzy_score",
    "normalise_token",
]
