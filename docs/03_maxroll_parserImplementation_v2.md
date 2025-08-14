# Maxroll Parser Implementation Plan v2

## 1. Analyze Implementation Plan and Requirements

- Review the original implementation plan and requirements for the maxroll_parser module.
- Ensure understanding of expected functionality, type safety, and SOLID compliance.

## 2. Audit Related Code and Docs for Dependencies

- Identify and review all files and modules that interact with or depend on maxroll_parser, including config, logging, and data layers.
- Check for existing usage patterns, configuration objects, and integration points.
- Key files: `config/settings.py`, `logging/setup.py`, `api/factory.py`, `api/dependencies.py`.

## 3. Review Current State of maxroll_parser Files

- Examine all files in `src/d3_item_salvager/maxroll_parser` (especially `get_guide_urls.py`, `guide_cache.py`, `types.py`, and any build/fetcher logic).
- Assess what is implemented, what is missing, and what needs refactoring.
- Findings: Main fetcher logic is missing from `get_guide_urls.py`; modular pipeline and API fetch logic exist in `guide_fetcher.py` and `guide_cleaner.py`; robust parsing in `build_profile_parser.py` and `item_data_parser.py`; `maxroll_client.py` is a central orchestrator but guide fetching is not yet integrated; cache utilities and type-safe data structures are present.

## 4. Design Class Structure and Interfaces for MaxrollGuideFetcher

- Class will accept config, logger, and cache utilities via dependency injection.
- Provides type-safe public methods: `fetch_guides` and `print_guides`.
- Uses modular pipeline for fetching, cleaning, and normalization.
- Integrates with cache utilities for file-based caching.
- Open for extension and testable.

## 5. Plan Guide Fetching and Normalization Logic

- Steps include checking cache, fetching from API if needed, deduplicating and normalizing guide data, handling errors with logging, and saving to cache.

## 6. Plan Caching and Error Handling Integration

- Caching uses `guide_cache.py` utilities, with TTL and location from config.
- Errors are logged using Loguru and handled gracefully, never crashing the app.
- Cache failures fall back to API fetch, ensuring robustness.

## 7. Plan Type-Safe Public Interfaces and Documentation

- All public methods and classes will use type annotations.
- Google-style docstrings will be provided for all public APIs.
- Interfaces will be documented for dependency injection and extensibility.
- Error handling and return types will be explicit.

## 8. Draft Implementation Steps and Testing Strategy

- Steps include implementing MaxrollGuideFetcher in `get_guide_urls.py`, integrating cache and error handling, writing type-safe interfaces and docstrings, and adding unit tests for all major logic.
- Plan for test coverage and validation of requirements.

---

This plan ensures robust, maintainable, and testable implementation for the maxroll_parser module, with all dependencies and integration points analyzed and documented.
