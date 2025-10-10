# API Endpoints Implementation

**Related Issue**: N/A

## Goal

Implement the initial FastAPI endpoints (`/items`, `/builds`, `/profiles`, `/item_usages`) described in `docs/11 apiImplementation.md`, providing filtering and pagination backed by the existing data/query layer while following project DI and testing conventions.

## High-Level Plan

Build typed response schemas and router functions that rely on the SQLModel session dependency, add or extend data query helpers to support flexible filtering with optional parameters, wire the routes into the FastAPI factory, and cover the new behavior with targeted API tests using dependency overrides and in-memory data fixtures. Update the API implementation document with any deviations or clarifications encountered during development.

## Public API Changes

- New GET endpoints: `/items`, `/builds`, `/profiles`, `/item_usages` with query parameters for filtering and pagination.
- OpenAPI schema gains corresponding models for list responses.

## Testing Plan

- Add unit-level API tests in `tests/api/` covering each endpoint, including filtering and pagination scenarios.
- Use dependency overrides to supply an in-memory SQLModel session seeded with representative data for deterministic responses.
- Run `scripts/check` to ensure lint, type checks, and tests all pass.

## Implementation Steps

- [x] Review existing data query helpers and extend them to cover filtering and pagination requirements.
- [x] Define Pydantic response schemas in a new `schemas.py` module under `src/d3_item_salvager/api/`.
- [x] Implement FastAPI route handlers for `/items`, `/builds`, `/profiles`, `/item_usages`, integrating with DI dependencies and query helpers.
- [x] Register the new routers in `create_app` and ensure CORS/docs configuration conforms to project conventions.
- [x] Write API endpoint tests with in-memory database fixtures validating success paths and edge cases.
- [x] Update `docs/11 apiImplementation.md` with any deviations, clarifications, or implementation notes discovered.
- [ ] Execute `scripts/check` and resolve any issues.

## Deviations

- `scripts/check` is not present in the repository; ran `uv run ruff check .`, `uv run pyright`, and `uv run pytest` instead. Pytest currently fails due to existing CLI configuration tests expecting a `maxroll_parser` validation error message that no longer matches actual output.
