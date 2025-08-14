# Maxroll Parser Implementation v3

## Overview

This specification defines the requirements, architecture, and implementation plan for a mature, type-safe, SOLID-compliant Maxroll parser module. The goal is to provide a unified, maintainable, and extensible pipeline for fetching guides, parsing build profiles, and extracting item usages for Diablo 3 builds.

## Goals

- Eliminate duplicate and immature code.
- Use robust, type-safe classes for all core features.
- Ensure single responsibility and clear separation of concerns.
- Provide a unified, high-level API for all Maxroll data operations.
- Support both API and local file sources for guides and profiles.
- Facilitate easy extension and testing.

## Core Features & Classes

### 1. Guide Fetching

- **Class:** `MaxrollGuideFetcher` (from `get_guide_urls.py`)
- **Responsibilities:**
  - Fetch guide metadata from Maxroll API or local files.
  - Return a list of typed `GuideInfo` objects.
  - Support configuration for API endpoints and file paths.

### 2. Build Profile Parsing

- **Class:** `BuildProfileParser` (from `build_profile_parser.py`)
- **Responsibilities:**
  - Load and parse build profile JSON files.
  - Extract normalized profiles as `BuildProfileData` objects.
  - Extract item usages as `BuildProfileItems` objects.
  - Robust error handling and validation.

### 3. Item Data Parsing

- **Class:** `DataParser` (from `item_data_parser.py`)
- **Responsibilities:**
  - Load and validate item data from `data.json`.
  - Provide item lookup and filtering.
  - Return typed item metadata for use in extraction.

### 4. Unified Orchestration

- **Class:** `MaxrollClient` (from `maxroll_client.py`)
- **Responsibilities:**
  - High-level API for fetching guides, profiles, and items.
  - Compose and coordinate the above classes.
  - Support plugin registration for extensibility.
  - Return only typed dataclasses for all outputs.

### 5. Data Models

- **Source:** `types.py`
- **Responsibilities:**
  - Define all data models as typed dataclasses: `GuideInfo`, `BuildProfileData`, `BuildProfileItems`.
  - Ensure type safety and clarity throughout the pipeline.

## SOLID Principles

- **Single Responsibility:** Each class has one clear purpose.
- **Open/Closed:** Classes are open for extension (via plugins, config), closed for modification.
- **Liskov Substitution:** Typed interfaces allow safe substitution and extension.
- **Interface Segregation:** Only expose necessary methods; avoid bloated interfaces.
- **Dependency Inversion:** High-level orchestration (`MaxrollClient`) depends on abstractions, not concrete implementations.

## Implementation Plan

1. **Remove all dict-based, duplicate, or immature classes/functions.**
2. **Refactor pipeline to use only the best classes:**
   - `MaxrollGuideFetcher` for guides
   - `BuildProfileParser` for profiles
   - `DataParser` for items
   - `MaxrollClient` for orchestration
   - `types.py` for all data models
3. **Update all usages and tests to use typed dataclasses.**
4. **Document all public APIs and data models.**
5. **Add comprehensive unit and integration tests.**
6. **Ensure all configuration is handled via dependency injection or config objects.**
7. **Provide clear error messages and robust validation throughout.**

## Example Usage

```python
from maxroll_parser.get_guide_urls import MaxrollGuideFetcher
from maxroll_parser.build_profile_parser import BuildProfileParser
from maxroll_parser.item_data_parser import DataParser
from maxroll_parser.maxroll_client import MaxrollClient
from maxroll_parser.types import GuideInfo, BuildProfileData, BuildProfileItems

# Initialize core components
guide_fetcher = MaxrollGuideFetcher(config)
profile_parser = BuildProfileParser(profile_path)
item_parser = DataParser(data_path)
client = MaxrollClient()

# Fetch guides
guides: list[GuideInfo] = guide_fetcher.fetch_guides()

# Parse build profiles
profiles: list[BuildProfileData] = profile_parser.profiles
items: list[BuildProfileItems] = profile_parser.extract_usages()

# Unified API
all_guides = client.get_guides()
all_profiles = client.get_build_profiles(profile_path)
item_data = client.get_item_data(item_id)
```

## Testing & Validation

- All classes must have unit tests covering edge cases and error handling.
- Integration tests must validate the full pipeline from guide fetch to item extraction.
- Type safety must be enforced via static analysis (e.g., mypy, pyright).
- All public APIs must be documented with usage examples.

## Migration & Cleanup

- Remove all legacy, dict-based, or duplicate code.
- Update documentation to reflect the new, unified pipeline.
- Ensure backward compatibility only if required; otherwise, prefer clean break.

## Future Extensions

- Support for additional game modes or guide sources.
- Plugin system for custom data extraction or transformation.
- Advanced caching and persistence strategies.

---
This spec ensures a maintainable, extensible, and type-safe Maxroll parser module for long-term use.
