# Diablo 3 Build Guide Item Scraper – Maxroll Parser Implementation Plan

## Overview

The `maxroll_parser` module is responsible for fetching, parsing, and caching Diablo 3 build guide data from Maxroll's Meilisearch API. It provides a class-based interface for guide retrieval, supports caching for efficiency, and is designed for extensibility to support future parsing and data extraction needs.

---

## Module Responsibilities

- Fetch build guide data from Maxroll's Meilisearch API.
- Deduplicate and normalize guide URLs and names.
- Cache guide data to minimize redundant API calls and improve performance.
- Provide a public interface for guide retrieval and printing.
- Log API interactions and errors for observability.
- Support configuration of API endpoint, bearer token, cache location, and cache TTL.
- Use type-safe data structures for guide information.

---

## Key Components

- **MaxrollGuideFetcher**: Main class for fetching and caching build guides.
  - Accepts configuration for API endpoint, bearer token, logger, cache TTL, and cache file location.
  - Loads cached guides on instantiation.
  - Fetches guides from API with deduplication and normalization.
  - Saves guides to cache after successful fetch.
  - Provides methods:
    - `fetch_guides(limit: int = 21) -> list[GuideInfo]`: Returns all guides, using cache if available.
    - `print_guides(limit: int = 21) -> None`: Prints guide names and URLs, plus total count.
- **GuideInfo**: Typed data structure for guide name and URL.
- **Cache Utilities**: Functions for loading and saving guides to cache (`load_guides_from_cache`, `save_guides_to_cache`).

---

## Design Expectations

- All guide URLs must be deduplicated and normalized to a consistent format.
- Guide names must be human-readable, with proper capitalization and formatting.
- Caching must use a file-based approach, with configurable TTL and location.
- API errors must be logged, and failures must not crash the application.
- The module must be extensible for future parsing needs (e.g., extracting additional guide metadata).
- All public interfaces must use type annotations and docstrings.
- The module must be testable, with clear separation between fetching, parsing, and caching logic.

---

## Directory Structure

```directory
src/
  d3_item_salvager/
    maxroll_parser/
      get_guide_urls.py           # Main fetcher class and logic
      get_guide_cache_utils.py    # Cache load/save utilities
      types.py                    # GuideInfo and related types
      ...                         # Additional parsing modules/extensions
docs/
  maxroll_parserImplementation.md # This design document

```

---

## Key Functions and Interfaces

- `MaxrollGuideFetcher.fetch_guides(limit: int = 21) -> list[GuideInfo]`
- `MaxrollGuideFetcher.print_guides(limit: int = 21) -> None`
- `load_guides_from_cache(path, ttl, logger) -> list[GuideInfo] | None`
- `save_guides_to_cache(guides, path, logger) -> None`
- `GuideInfo`: Typed structure for guide name and URL

---

## Extensibility and Integration

- The module is designed to support future extensions for parsing additional guide data, integrating with other data layers, and supporting new caching strategies.
- Integration with the broader data and API layers is supported via typed interfaces and clear separation of concerns.

---

## Best Practices

- Use type annotations and docstrings for all public interfaces.
- Log all API interactions and errors.
- Deduplicate and normalize all guide data.
- Use caching to minimize redundant API calls.
- Structure code for testability and extensibility.

---

## Requirements Summary

- Fetch, deduplicate, and normalize Diablo 3 build guide data from Maxroll's API.
- Cache guide data with configurable TTL and location.
- Provide type-safe, documented public interfaces for guide retrieval and printing.
- Log errors and support robust, extensible design for future parsing needs.
