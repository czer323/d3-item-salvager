"""Filtering utilities shared by frontend services and client scripts."""

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


@dataclass(frozen=True, slots=True)
class PaginationState:
    """Metadata describing the pagination applied to a result set."""

    page: int
    page_size: int
    total_items: int

    @property
    def page_count(self) -> int:
        """Return the total number of pages available."""
        if self.page_size <= 0:
            return 1
        pages, remainder = divmod(self.total_items, self.page_size)
        return pages + (1 if remainder else 0) or 1

    @property
    def has_previous(self) -> bool:
        """Return True when a previous page exists."""
        return self.page > 1

    @property
    def has_next(self) -> bool:
        """Return True when a subsequent page exists."""
        return self.page < self.page_count


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


def paginate_items[TFiltered: SupportsFiltering](
    items: Sequence[TFiltered],
    *,
    page: int,
    page_size: int,
) -> tuple[list[TFiltered], PaginationState]:
    """Paginate a sequence, returning the current slice and metadata."""
    total_items = len(items)
    safe_page_size = max(1, page_size)
    max_page = max(1, (total_items + safe_page_size - 1) // safe_page_size)
    safe_page = min(max(page, 1), max_page)

    start_index = (safe_page - 1) * safe_page_size
    end_index = start_index + safe_page_size
    active_items = list(items[start_index:end_index])
    pagination = PaginationState(
        page=safe_page,
        page_size=safe_page_size,
        total_items=total_items,
    )
    return active_items, pagination


def parse_page(value: str | None, *, default: int = 1) -> int:
    """Parse a page number from a string, enforcing positive bounds."""
    if value is None:
        return max(1, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return max(1, default)
    return parsed if parsed > 0 else 1


def parse_page_size(
    value: str | None,
    *,
    default: int = 60,
    minimum: int = 5,
    maximum: int = 200,
) -> int:
    """Parse and clamp an incoming page size value."""
    if value is None:
        return _clamp(default, minimum, maximum)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return _clamp(default, minimum, maximum)
    return _clamp(parsed, minimum, maximum)


def _normalise_token(value: str | None) -> str:
    if not value:
        return ""
    return "".join(char for char in value.casefold() if char.isalnum())


def _clamp(value: int, minimum: int, maximum: int) -> int:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


__all__ = [
    "FilterCriteria",
    "PaginationState",
    "SupportsFiltering",
    "apply_filters",
    "fuzzy_score",
    "paginate_items",
    "parse_page",
    "parse_page_size",
]
