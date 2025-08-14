# Maxroll Parser Protocol Compliance & Type Safety Implementation Plan (v4)

## Overview

This document outlines the step-by-step plan for achieving full protocol compliance, type safety, and robust testing in the `maxroll_parser` package. The goal is to ensure all main classes and their dependencies adhere to the contracts defined in `protocols.py`, use protocol types for dependency injection, and are fully covered by a protocol-driven test suite.

---

## Step-by-Step Plan

### 1. Audit Main Classes for Protocol Mapping

- Identify all main classes in the following files:
  - `build_profile_parser.py`
  - `guide_cache.py`
  - `get_guide_urls.py`
  - `item_data_parser.py`
  - `maxroll_client.py`
- For each class, determine which protocol(s) from `protocols.py` it should implement based on its responsibilities and public API.

### 2. Document Protocol Requirements for Each Class

- For each class, list the required methods and attributes from the relevant protocol(s).
- Note any missing or incorrectly typed methods/attributes that need to be added or refactored.

#### Identified Classes and Their Protocols

| File                   | Class                | Protocol(s) to Implement         | Notes on Compliance |
|------------------------|---------------------|----------------------------------|---------------------|
| build_profile_parser.py| BuildProfileParser  | BuildProfileParserProtocol       | Needs: `extract_usages`, `parse_profile` methods, ensure `profiles` attribute is typed and public |
| guide_cache.py         | FileGuideCache      | GuideCacheProtocol               | Already matches protocol, confirm method signatures and type annotations |
| get_guide_urls.py      | MaxrollGuideFetcher | GuideFetcherProtocol             | Already matches protocol, confirm method signatures and type annotations |
| item_data_parser.py    | DataParser          | ItemDataParserProtocol           | Needs: `get_item`, `get_all_items` methods, ensure correct return types |
| maxroll_client.py      | MaxrollClient       | Aggregates all above protocols   | Should use protocol types for attributes, DI, and return values |

**Recommendations:**

- Refactor each class to explicitly implement its protocol (via inheritance or type annotation).
- Ensure all required protocol methods/attributes are present and correctly typed.
- Use protocol types for dependency injection, factory, and client code.
- Update tests to use protocol types for mocks/fakes and DI.
- Document public APIs and DI points with protocol types for clarity and maintainability.

### 3. Protocol Mapping and Requirements

#### build_profile_parser.py

- **Should implement:** `BuildProfileParserProtocol`
- **Required:**
  - `profiles: list[BuildProfileData]`
  - `extract_usages() -> list[BuildProfileItems]`
  - `parse_profile(file_path: str) -> object`

#### guide_cache.py

- **Should implement:** `GuideCacheProtocol`
- **Required:**
  - `load() -> list[GuideInfo] | None`
  - `save(guides: Iterable[GuideInfo]) -> None`

#### get_guide_urls.py

- **Should implement:** `GuideFetcherProtocol`
- **Required:**
  - `fetch_guides(search: str | None = None, *, force_refresh: bool = False) -> list[Any]`
  - `get_guide_by_id(guide_id: str) -> GuideInfo | None`

#### item_data_parser.py

- **Should implement:** `ItemDataParserProtocol`
- **Required:**
  - `get_item(item_id: str) -> ItemMeta | None`
  - `get_all_items() -> Mapping[str, ItemMeta]`

#### maxroll_client.py

- **Should aggregate or delegate:** All above protocols
- **Required:**
  - Attributes or methods typed as protocol interfaces
  - Dependency injection and return values use protocol types

### 4. Concrete Refactoring Actions

- Refactor each class to inherit from its relevant protocol(s).
- Ensure all required attributes and methods are present and correctly typed.
- Use protocol types for type annotations in DI, factories, and client code.
- Refactor DI/factory code to use protocol types for instantiation and registration.
- Ensure all code that passes dependencies uses protocol types.

### 5. Test Suite Refactoring Actions

- Refactor all existing tests to use protocol types for mocks, fakes, and dependency injection.
- For each main class, create or update test cases that:
  - Inject dependencies using protocol types (not concrete classes).
  - Assert correct behavior for all protocol methods.
  - Use containers or fixtures to manage protocol-driven dependencies.
- Add/expand tests to cover edge cases and contract enforcement for each protocol.
- Ensure all tests pass and provide coverage for protocol-driven architecture.

### 6. Static Type Checking, Linting, and Final Validation

- Run static type checkers (Pyright, MyPy) on the entire codebase to ensure all protocol implementations and type annotations are correct.
- Run linting tools (ruff, pylint) to confirm code style and quality.
- Fix any errors or warnings reported by type checkers or linters.
- Ensure all tests pass (unit, integration, e2e) with protocol-based architecture.
- Review deliverables for completeness: updated source files, protocol-driven test suite, and documentation.

---

## Success Criteria

- All main classes explicitly implement and use the relevant protocols.
- All dependency injection, factory, and client code use protocol types for attributes, constructor parameters, and return values.
- All code passes linting and static type checks.
- All tests pass with protocol-based architecture.
- Documentation and public APIs reference protocol types.

---

## Next Steps

- Execute the plan for each file and test suite.
- Validate with static analysis and test runs.
- Update this document with implementation notes and lessons learned.
