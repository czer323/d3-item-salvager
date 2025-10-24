# Tasks: Design a frontend application for d3-item-salvager

**Input**: Design documents from `specs/001-design-a-frontend/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Required per FR-010. Tests appear in each user story phase.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Task can run in parallel (different files, no dependencies)
- **[Story]**: Story or phase label (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish frontend project skeleton and dependencies

- [x] T001 [Setup] Create frontend skeleton with entrypoint and package dirs (`frontend/app.py`, `frontend/__init__.py`, `frontend/src/__init__.py`, `frontend/templates/.gitkeep`, `frontend/static/.gitkeep`, `frontend/tests/__init__.py`).
- [x] T002 [Setup] Update `pyproject.toml` to declare frontend dependencies (`flask`, `jinja2`, `httpx`, `python-dotenv`, `playwright`, `pytest-playwright`) and refresh the lockfile with `uv lock`.
- [x] T003 [Setup] Scaffold Playwright test runner (`frontend/tests/playwright/playwright.config.ts`, `frontend/tests/playwright/__init__.py`) with base URL configuration pointing at the Flask frontend dev server.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure required before any user story work

- [x] T004 [Foundational] Create immutable configuration dataclass for frontend settings in `frontend/src/config.py` (includes backend base URL, timeout, feature flags).
- [x] T005 [Foundational] Implement HTTP client wrapper using `httpx` in `frontend/src/services/backend_client.py` with retry/backoff and error translation helpers.
- [x] T006 [Foundational] Implement Flask app factory in `frontend/app.py` that loads config, registers blueprints, configures Jinja2, and exposes `create_app()`.
- [x] T007 [Foundational] Scaffold routing package (`frontend/src/routes/__init__.py`, `frontend/src/routes/base.py`) with blueprint registration and root index route placeholder.
- [x] T008 [Foundational] Create shared layout template with Tailwind + DaisyUI + HTMX CDN links in `frontend/templates/layout/base.html` including global nav and focus styles.
- [x] T009 [Foundational] Add reusable error/empty-state partials in `frontend/templates/components/error_state.html` for backend outages and `frontend/templates/components/loading_spinner.html` for HTMX swaps.
- [x] T010 [Foundational] Provide pytest/Playwright fixtures in `frontend/tests/conftest.py` to launch the Flask app on an ephemeral port for UI and contract tests.

**Checkpoint**: Foundation ready—user story implementation can begin.

---

## Phase 3: User Story 1 - Show build items and salvage candidates (Priority: P1) 🎯 MVP

**Goal**: Display selected builds' required items and a separate salvage list with clear labeling.

**Independent Test**: Select class/build/variant set; verify "Used by selected builds" and "Not used / Salvage candidates" sections match reference data counts and labels.

### Tests for User Story 1 (write first)

- [x] T011 [P] [US1] Add OpenAPI contract test for `/frontend/variant/{variant_id}.json` in `frontend/tests/contracts/test_variant_endpoint.py` validating schema from `specs/001-design-a-frontend/contracts/variant.json`.
- [x] T012 [P] [US1] Create Playwright journey `frontend/tests/playwright/test_variant_summary.py` covering selection → summary view with keep/salvage assertions.

### Implementation for User Story 1

- [x] T013 [US1] Implement salvage classification helper in `frontend/src/services/salvage_classifier.py` to tag items (Keep, Salvage, Kanai, Follower).
- [x] T014 [US1] Implement variant summary aggregator in `frontend/src/services/variant_summary.py` to compose backend data, deduplicate items, and split used vs salvage lists.
- [x] T015 [US1] Implement variant routes and JSON-mode endpoint in `frontend/src/routes/variants.py`, including graceful handling for backend timeouts (uses error partial).
- [x] T016 [US1] Build variant summary templates (`frontend/templates/variants/summary.html`, `frontend/templates/variants/sections.html`) rendering used vs salvage sections with slot grouping and badges.
- [x] T017 [US1] Create dashboard page template in `frontend/templates/pages/dashboard.html` that extends the base layout and includes HTMX target containers for summary content.

**Checkpoint**: User Story 1 complete—summary view and JSON contract work end-to-end.

---

## Phase 4: User Story 2 - Select classes, builds and variants (Priority: P1)

**Goal**: Provide selector UI for classes/builds/variants that drives the summary view.

**Independent Test**: Choose class/build/variant combinations; summary updates immediately to reflect choices with deduplicated items.

### Tests for User Story 2 (write first)

- [x] T018 [P] [US2] Add Playwright journey `frontend/tests/playwright/test_selection_controls.py` verifying selector interactions refresh the summary list.
- [x] T019 [P] [US2] Add unit test `frontend/tests/unit/test_selection_view.py` ensuring selection view model groups build guides by class and marks selected options.

### Implementation for User Story 2

- [x] T020 [US2] Implement selection data service in `frontend/src/services/selection.py` to fetch build guides/variants and map them to selector view models.
- [x] T021 [US2] Add selection routes & HTMX endpoints in `frontend/src/routes/selection.py` serving selectors and triggering summary refresh events.
- [x] T022 [US2] Create selector templates (`frontend/templates/selection/controls.html`, `frontend/templates/selection/option_group.html`) with DaisyUI components and HTMX triggers.
- [x] T023 [US2] Update `frontend/templates/pages/dashboard.html` to embed selection controls, wire HTMX requests to `/frontend/variant/{variant_id}` endpoints, and ensure deduped state flows into summary.

**Checkpoint**: User Stories 1 & 2 functional—core MVP ready for feedback.

---

## Phase 5: User Story 3 - Save selected classes/builds/variants as preferences (Priority: P2)

**Goal**: Persist selections locally with import/export capabilities.

**Independent Test**: Save selections, reload the app, and confirm preferences auto-apply; export/import JSON restores same selections.

### Tests for User Story 3 (write first)

- [x] T024 [P] [US3] Add Playwright test `frontend/tests/playwright/test_preferences_persistence.ts` validating save → reload → restore flow and JSON import/export.
- [x] T025 [P] [US3] Add unit test `frontend/tests/unit/test_preferences.py` covering serialization, versioning, and validation of preferences payloads.

### Implementation for User Story 3

- [x] T026 [US3] Implement preferences service in `frontend/src/services/preferences.py` to format defaults, enforce versioning, and provide import/export helpers.
- [x] T027 [US3] Create client script `frontend/static/js/preferences.js` handling localStorage persistence, HTMX event integration, and import/export actions.
- [x] T028 [US3] Add preferences modal and controls in `frontend/templates/selection/preferences_modal.html` with save/export/import buttons and status toasts.
- [x] T029 [US3] Integrate preferences controls into `frontend/templates/layout/base.html` and `frontend/templates/pages/dashboard.html`, binding JS hooks and ensuring initial load reads saved state.

**Checkpoint**: User Story 3 validated—preferences persist and import/export works.

---

## Phase 6: User Story 4 - Realtime fuzzy search and slot filter (Priority: P2)

**Goal**: Provide realtime fuzzy search and slot filtering across item lists.

**Independent Test**: Typing partial item names filters results instantly; applying slot filter narrows items, with empty-state messaging when nothing matches.

### Tests for User Story 4 (write first)

- [ ] T030 [P] [US4] Add Playwright test `frontend/tests/playwright/test_item_filtering.py` covering fuzzy search + slot filter interactions and empty-state messaging.
- [ ] T031 [P] [US4] Add unit test `frontend/tests/unit/test_filtering.py` for fuzzy scoring and slot filter combinations used by client script.

### Implementation for User Story 4

- [ ] T032 [US4] Implement client-side filtering utility in `frontend/static/js/filtering.js` with lightweight fuzzy matching and HTMX debounce hooks.
- [ ] T033 [US4] Extend `frontend/src/routes/variants.py` and `frontend/src/services/variant_summary.py` to surface slot metadata, accept search/filter params, and paginate large result sets for HTMX partial loads.
- [ ] T034 [US4] Update summary templates (`frontend/templates/variants/summary.html`, `frontend/templates/components/empty_state.html`, `frontend/templates/components/filter_controls.html`) to include search box, slot filter, and "No items found" messaging.

**Checkpoint**: User Story 4 complete—search and filter experience fully functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation, resilience, and quality gates across stories

- [ ] T035 [P] [Polish] Update `frontend/README.md` with final run, test, and dependency instructions aligned with Playwright setup.
- [ ] T036 [P] [Polish] Refresh `specs/001-design-a-frontend/quickstart.md` to document the finalized dev server command, HTMX endpoints, and smoke test steps.
- [ ] T037 [Polish] Audit templates (`frontend/templates/layout/base.html`, `frontend/templates/pages/dashboard.html`, `frontend/templates/variants/summary.html`) for accessibility (ARIA labels, focus order, contrast) and responsive breakpoints.
- [ ] T038 [Polish] Add Playwright regression `frontend/tests/playwright/test_backend_error_state.py` asserting offline/error handling renders the shared error partial with retry CTA.
- [ ] T039 [Polish] Execute `uv run pre-commit run --all-files`, capture logs under `precommit_logs/frontend_tasks.txt`, and fix any lint/type/test failures.

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** → unlocks all user stories.
- **User Story Order**: US1 (P1) → US2 (P1) can proceed in parallel once foundational tasks finish; US3 (P2) and US4 (P2) depend on selectors and summary to exist (preferred order US1 → US2 → US3 → US4).
- **Polish (Phase 7)** depends on completion of all targeted user stories and tests.
- Within each story, tests (Playwright/unit/contract) run before implementation tasks to follow TDD expectations.

## Parallel Execution Examples

- **US1**: After T011 starts, T012 can run in parallel; once tests are ready, T013 (salvage helper) and T016 (templates) can progress alongside T015 (routes) by separate contributors.
- **US2**: T018 and T019 can execute simultaneously; T020 (service) and T022 (templates) can proceed in parallel once the data contract is agreed.
- **US3**: T024 and T025 can run together; T027 (JS) can progress in parallel with T026 (service) after API schema is defined.
- **US4**: T030 and T031 are independent; T032 (client utility) can run while T033 updates server logic, with coordination on filter event names.

## Implementation Strategy

- **MVP First**: Deliver Phases 1–4 (through US2) to produce a demo-ready salvage dashboard with live selectors.
- **Incremental Enhancements**: Layer in preferences (Phase 5) followed by search/filter UX (Phase 6) once MVP is stable.
- **Quality Gates**: Keep Playwright tests green per story, run `uv run pyright` and `uv run pytest` after each phase, and ensure documentation stays current (Phase 7).
- **Risk Mitigation**: Use the JSON-mode endpoint from US1 for deterministic smoke tests; leverage shared error partial to surface backend outages consistently.
