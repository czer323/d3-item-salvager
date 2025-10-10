# Services Module Completion

**Related Issue**: n/a

## Goal

Complete the services module as outlined in `docs/09 servicesImplementationv2.md`, delivering a production-ready `BuildGuideService` (and related helpers) wired for dependency injection, with tests and documentation.

## High-Level Plan

- Formalize the dependency contracts (logger, guide fetcher, profile parser, item data lookup, SQLModel session factory) that the service will accept via DI.
- Refactor `BuildGuideService` into small, stateless public methods (fetch, parse, persist) while keeping a high-level orchestration helper.
- Introduce adapter utilities that convert parsed `BuildProfileData` / `BuildProfileItems` objects into the SQLModel entities expected by `d3_item_salvager.data.loader`.
- Replace brittle SQL string execution with SQLModel primitives and tighten logging/error handling around database writes.
- Ensure the DI container exposes configured services and logger, and align other service stubs (e.g., `ItemSalvageService`) with project conventions.
- Back the new service logic with unit tests (fakes) and an integration test using an in-memory database.
- Update documentation and docstrings to describe the public API intended for workers.

## Public API Changes

- New/expanded public methods on `BuildGuideService` (`fetch_guides`, `build_profiles_from_guides`, `sync_profiles_to_database`, plus orchestration helper).
- Optional `ServiceLogger` protocol to describe the logging dependency.
- Container wiring additions for the service and logger setup.

## Testing Plan

- Unit: mock/fake fetcher, parser, item data provider, and verify service behavior/branching.
- Integration: run service against in-memory SQLModel session to validate inserts via loader helpers.
- Static checks: ensure `scripts/check` passes (lint, type, tests).

## Implementation Steps

- [x] Capture and document the concrete DI dependencies; define protocols/types in `services` package as needed.
- [x] Refactor `BuildGuideService` into discrete public methods plus an orchestration wrapper, using the new contracts.
- [x] Implement adapter utilities to map parser outputs to SQLModel models and update DB insertion logic for type safety.
- [x] Harden logging/error handling and swap raw SQL execution for SQLModel expressions, maintaining idempotency safeguards.
- [x] Align `ItemSalvageService` (or replace with TODO/TBD) to meet project conventions and avoid dead stubs.
- [x] Update DI container/providers to expose the finalized services and ensure logger setup is applied.
- [x] Add unit and integration tests under `tests/services/` covering success paths and failure scenarios.
- [x] Refresh documentation (service docstrings, `docs/09 servicesImplementationv2.md` status) and run `scripts/check`.

## Deviations

_None yet._
