# Tasks: Frontend UI Redesign - Selection & Item List

This tasks.md follows the speckit tasks format. Tasks are grouped into phases and organized by user story where applicable. Each task is a single, actionable PR-sized item with a unique TaskID and file path where code or docs should be changed.

---

Phase 1 — Setup

- [x] T001 [P] Create contracts directory and add initial contracts in `specs/002-frontend-ui-redesign/contracts/` (`build-items.json`, `items-lookup.json`) — `specs/002-frontend-ui-redesign/contracts/`
- [ ] T002 Add quickstart and README entries for the feature (`specs/002-frontend-ui-redesign/quickstart.md`, `README.md`) — `specs/002-frontend-ui-redesign/quickstart.md`, `specs/002-frontend-ui-redesign/README.md`
- [x] T003 [P] Add research notes and link to existing fuzzy impl (`specs/002-frontend-ui-redesign/research.md`) — `specs/002-frontend-ui-redesign/research.md`

Phase 2 — Foundational / Backend (blocking)

- [x] T004 [US3] [P] Port `fuzzy_score` into a backend shared util at `src/d3_item_salvager/utility/search.py` with unit tests mirroring frontend tests — `src/d3_item_salvager/utility/search.py`, `tests/unit/test_search.py`
- [x] T005 [P] Implement `GET /items/lookup` API endpoint returning `SearchResult` (match_type, item, suggestions, salvageable) and wire to shared search util — `src/d3_item_salvager/api/endpoints.py`, `src/d3_item_salvager/api/schemas.py`, `tests/integration/test_items_lookup.py`
- [x] T006 [P] Implement `GET /builds/items?build_ids=...` API endpoint that returns the union of items for provided build ids (de-duplicated, alphabetical, paginated) — `src/d3_item_salvager/api/endpoints.py`, `tests/integration/test_builds_items.py`
- [x] T007 Add backend unit & contract tests for T005/T006 and ensure OpenAPI matches `specs/002-frontend-ui-redesign/contracts/` — `tests/contract/`, `tests/unit/`

Phase 3 — Frontend: Selection UI (US1)

- [x] T008 [US1] Create the inline collapsible selection panel template and HTMX partial: `frontend/templates/selection_panel.html` and `frontend/src/components/selection.js` — `frontend/templates/selection_panel.html`, `frontend/src/components/selection.js`
- [x] T009 [US1] Implement selection summary bar (collapsed state) with an Edit affordance and keyboard accessible controls — `frontend/templates/selection_summary.html`, `frontend/src/components/selection.js`
- [x] T010 [US1] Add unit tests for selection UI flows (open/collapse, keyboard navigation) — `frontend/tests/unit/test_selection.py`

Phase 4 — Frontend: Item list population (US2)

- [ ] T011 [US2] Implement client call to `GET /builds/items` to fetch the union list when selection changes; render results in `frontend/templates/item_list.html` — `frontend/src/services/builds.js`, `frontend/templates/item_list.html`
- [ ] T012 [US2] Ensure de-duplication and alphabetical ordering (prefer server-side ordering; add client-side sanity check) — `frontend/src/services/builds.js`, `src/d3_item_salvager/data/queries.py`
- [ ] T013 [US2] Add virtualization/pagination for the item list (use existing patterns or implement small virtual list) — `frontend/src/components/virtual_list.js`, `frontend/templates/item_list.html`
- [ ] T014 [US2] Add integration tests to validate union behavior with multiple build selections — `tests/integration/test_union_items.py`, `frontend/tests/e2e/test_union_items.spec.ts`

Phase 5 — Frontend: Search & Validation (US3)

- [ ] T015 [US3] Hook up search box to `GET /items/lookup`; implement search result UI (exact highlight, fuzzy suggestions dropdown, salvageable state) — `frontend/src/components/search.js`, `frontend/templates/search.html`
- [ ] T016 [US3] Add affordance buttons to add a suggested item to the current selection or mark as salvageable and persist to browser `localStorage` so selections persist across refreshes — `frontend/src/components/search.js`, `frontend/src/services/preferences.js`
- [ ] T017 [US3] Add unit and integration tests for search behaviors (exact, fuzzy, none) — `frontend/tests/unit/test_search.py`, `tests/integration/test_search_integration.py`

Phase 6 — Frontend: Item Table & Filters (US4)

- [ ] T018 [US4] Implement item table row rendering with Name (color + icon + ARIA label), Class (single/multi), Usage chips (main, follower, kanai) — `frontend/templates/item_row.html`, `frontend/src/components/item_row.js`
- [ ] T019 [US4] Add CSS styles and utility classes: set (green) and legendary (orange) with accessible contrast + icons — `frontend/static/css/components.css` or Tailwind utilities
- [ ] T020 [US4] Implement sorting by Name (ascending/descending toggle) and client-side usage filters (show-only-main, hide-other-usages) — `frontend/src/components/table_sort_filter.js`
- [ ] T021 [US4] Add unit tests for table rendering, sorting and usage filter behaviors — `frontend/tests/unit/test_table.py`

Phase 7 — Integration, QA & Accessibility

- [ ] T022 [P] Add Playwright e2e tests covering primary flows end-to-end (US1-US4) — `frontend/tests/e2e/`
- [ ] T023 Accessibility: Add axe checks and fix keyboard/ARIA issues; add automated accessibility tests — `frontend/tests/accessibility/test_accessibility.py`
- [ ] T024 Performance & scale: Add test that verifies responsiveness for large lists; ensure virtualization/pagination behavior — `frontend/tests/performance/test_large_list.py`

<!-- INSERT: NEW TEST & PERSISTENCE TASKS - BEGIN -->
- [ ] T028 [P] Persist selection state (MUST, test-first): Persist selection across full page reloads and soft navigations; **tests:** `tests/integration/selection/test_persistence.py` (integration; test-first).

- [ ] T029 [P] Fuzzy thresholds & typo corpus (test-first): Define thresholds, create the small typo corpus, and add deterministic unit tests for the 6 canonical cases; **tests:** `tests/unit/filtering/test_fuzzy_thresholds.py` (unit; test-first).

- [ ] T030 [P] Initial-render performance tests (test-first): Add Playwright-based e2e tests measuring TTI and asserting median ≤ 300 ms; **tests:** `tests/e2e/performance/test_initial_render.spec.ts` (Playwright; test-first).

- [ ] T031 [P] Items lookup latency tests (test-first): Add client-side keystroke→suggestions and server-side instrumented latency tests; **tests:** `tests/e2e/performance/test_items_lookup_latency.spec.ts` & `tests/integration/metrics/test_items_lookup_latency.py` (e2e + integration; test-first).

- [ ] T032 [P] Add per-task test-first subtasks: Create failing test placeholders for each implementation task (T004-T021) and track them as T004a..T021a. Example: T004a write failing tests for T004 in `tests/unit/...` (test-first).

### Phase 2–6 — Test-first subtasks (explicit placeholders)

- [x] T004a [P] Write failing unit tests for the backend fuzzy util (T004); `tests/unit/filtering/test_search_util.py` (test-first)
- [x] T005a [P] Write failing integration tests for `/items/lookup` (T005); `tests/integration/test_items_lookup.py` (test-first)
- [x] T006a [P] Write failing integration tests for `/builds/items` (T006); `tests/integration/test_builds_items.py` (test-first)
- [x] T008a [P] Write failing unit/integration tests for selection panel behaviors (T008); `frontend/tests/unit/test_selection_panel.py` (test-first)
- [x] T009a [P] Write failing tests for selection summary and collapse (T009); `frontend/tests/unit/test_selection_summary.py` (test-first)
- [x] T010a [P] Write failing keyboard/accessibility tests for selection flows (T010); `frontend/tests/unit/test_selection_keyboard.py` (test-first)
- [ ] T011a [P] Write failing integration tests for builds/items client fetch (T011); `tests/integration/test_fetch_build_items.py` (test-first)
- [ ] T012a [P] Write failing tests for de-duplication and ordering (T012); `tests/unit/test_de_duplication.py` (test-first)
- [ ] T013a [P] Write failing tests for virtualization/pagination behavior (T013); `frontend/tests/unit/test_virtual_list.py` (test-first)
- [ ] T014a [P] Write failing integration tests for union behavior (T014); `tests/integration/test_union_items.py` (test-first)
- [ ] T015a [P] Write failing unit/integration tests for search UI & lookup integration (T015); `frontend/tests/unit/test_search_ui.py`, `tests/integration/test_search_integration.py` (test-first)
- [ ] T016a [P] Write failing tests for add-to-selection and salvage flows (T016); `frontend/tests/unit/test_search_actions.py` (test-first)
- [ ] T017a [P] Write failing tests for search behaviors (T017); `frontend/tests/unit/test_search_behavior.py` (test-first)
- [ ] T018a [P] Write failing unit tests for item row rendering and ARIA (T018); `frontend/tests/unit/test_item_row.py` (test-first)
- [ ] T019a [P] Write failing accessibility/contrast tests for CSS utilities (T019); `frontend/tests/unit/test_css_contrast.py` (test-first)
- [ ] T020a [P] Write failing tests for sorting and usage filters (T020); `frontend/tests/unit/test_table_sort_filter.py` (test-first)
- [ ] T021a [P] Write failing tests for table rendering and integration (T021); `frontend/tests/unit/test_table_render.py` (test-first)
- [ ] T032a [P] Verify test-first subtasks exist and are failing on baseline; `scripts/ci/check_test_first.py` (chore)

<!-- INSERT: NEW TEST & PERSISTENCE TASKS - END -->

Phase 8 — Release Prep

- [ ] T025 Update documentation, quickstart and changelog (`specs/002-frontend-ui-redesign/quickstart.md`, README, CHANGELOG.md) — `specs/002-frontend-ui-redesign/quickstart.md`, `CHANGELOG.md`
- [ ] T026 Run pre-commit, pyright, and full test-suite; fix all issues — (CI / local) — no specific file
- [ ] T027 Prepare PR with description, checklist, and request reviews — GitHub PR

---

Notes:
- Mark tasks completed in this file as you complete them and create PRs for each completed task.
- If a task is parallelizable without conflicting files, mark it with `[P]`.
- Tasks that correspond to specific user stories include `[US1]`–`[US4]` labels.

If you'd like, I can now open the first branch and start with T004 (adding the backend fuzzy util & tests). Reply with "Start T004" to proceed.
