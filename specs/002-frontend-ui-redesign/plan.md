# Implementation Plan: Frontend UI Redesign - Selection & Item List

**Branch**: `002-frontend-ui-redesign` | **Date**: 2026-01-03 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/002-frontend-ui-redesign/spec.md` and data-model at `specs/001-design-a-frontend/data-model.md`.

---

## Summary

Improve the selection UI and item-list visualization with minimal backend disruption:
- Inline, collapsible class/build selection panel supporting multi-class + multi-build selection (default visible when no selection/search performed).
- Item list populated as the union of selected class(es)/build(s) items (alphabetical), client-side search validation backed by a backend lookup using the repository's fuzzy algorithm.
- Table view: `Name` (color + icon + ARIA), `Class` (single/multiple), `Usage` (multi-valued chips). Remove variants count; provide sorting and usage filters.

Start from existing data models and contracts (see `data-model.md` and `specs/001-design-a-frontend/contracts/variant.json`) and add minimal additive endpoints only where necessary.

---

## Technical Context

- Language: Python 3.12+ (backend)
- Backend: FastAPI + SQLModel
- Frontend: Jinja2 + HTMX, Tailwind / DaisyUI existing patterns
- Testing: pytest (unit), Playwright (e2e), axe (accessibility checks)
- Storage: No new permanent storage required (use session/localStorage for UI prefs)
- Performance: client-side virtualization or server pagination for large union lists (NFR-002)

Key existing artifacts:
- `specs/001-design-a-frontend/data-model.md` (entity definitions) — note: item `quality` (string: 'set'|'legendary') is the canonical indicator for set vs legendary and is mutually exclusive.
- `specs/001-design-a-frontend/contracts/variant.json` (existing frontend test contract for variant payload)
- `frontend/src/services/filtering.py::fuzzy_score` (current fuzzy algorithm)

Storage and UX notes:
- Selection state SHOULD persist across page reloads using browser localStorage so the collapsed/expanded selection panel and recent choices remain after refresh.

---

## Constitution Check (Gates)

- Library-first compliance: OK — feature implemented as a frontend subproject, small backend additions documented in contracts. ✔️
- Testing plan: OK — unit + integration + Playwright tests required. ✔️
- Contracts: Add two new contracts (`build-items.json`, `items-lookup.json`) and ensure they are small and additive. ✔️
- Versioning impact: None expected for current endpoints; new endpoints will be additive and documented. ✔️

<!-- INSERT: TEST-FIRST ENFORCEMENT - BEGIN -->
#### Test-First Enforcement ✅
To enforce the project's constitution (*Test-First is NON-NEGOTIABLE*):
- All Phase 2–6 implementation tasks (T004–T021) **must** have corresponding failing tests authored and committed prior to feature implementation.
- CI gating: PRs that add implementation without existing failing tests will be blocked; reviewers must verify that test-first tasks exist and fail on the PR baseline.
- Teams should create failing test placeholders (unit/integration/e2e as appropriate) that assert the required behavior before implementing the feature.

Deliverable: add per-task test-first subtasks (T004a, T005a, …) to track and confirm completion.
<!-- INSERT: TEST-FIRST ENFORCEMENT - END -->

...

---

## Phases & Deliverables

### Phase 0 — Research & Discovery (complete)
Deliverables: `research.md` (this contains findings about `fuzzy_score`, endpoints to reuse, and initial design notes).
Key outcomes: Identify the canonical `fuzzy_score` implementation at `frontend/src/services/filtering.py::fuzzy_score`. Plan to review and either reuse or migrate the implementation into a backend utility with **unit-test parity** and to align behavior with the thresholds defined in `spec.md` (FR-004 clarification).

### Phase 1 — API & Contracts (design → implement)
Deliverables: OpenAPI contract files added to `specs/002-frontend-ui-redesign/contracts/`:
- `build-items.json` (GET /builds/items?build_ids=1,2)
- `items-lookup.json` (GET /items/lookup?query=...)

Backend: Implement two read-only endpoints (additive, backward compatible) and shared fuzzy util in `d3_item_salvager.utility.search` with unit tests.

### Phase 2 — Frontend Implementation
Deliverables: HTMX/Jinja2 templates and small UI components:
- Collapsible selection panel with multi-class & multi-build support + summary bar
- Item list population (union of selected builds/classes), alphabetical ordering
- Search validation UI wired to `/items/lookup`
- Item table with Name color/icon/ARIA, Class column, Usage chips, sorting, and usage filters
- Client-side virtualization/pagination or server-driven pagination if needed

### Phase 3 — Integration & QA
Deliverables: Playwright tests, accessibility pass (axe), performance checks, updated spec and quickstart.

### Phase 4 — Release & Documentation
Deliverables: PR with tests, updated spec, CHANGELOG entry and deployment notes.

---

## Acceptance Criteria (mapped to spec)
- The selection UI collapses after selection and is re-expandable (FR-002). ✅
- Multiple classes and builds can be selected; item list is the union (no duplicates) and alphabetical (FR-001, FR-003, FR-007). ✅
- Search resolves exact/fuzzy/none and provides clear results and salvage affordance (FR-004, FR-009). ✅
- Item table has requested columns and behaviors; no variants count (FR-005, FR-006, FR-008). ✅
- Accessibility checks pass and performance targets met per NFRs. ✅

---

## Risks & Mitigations
- Divergent fuzzy behavior after moving util: ensure unit test parity and reuse logic.
- Adding endpoints increases API surface: keep endpoints read-only and small; document in contracts.
- Large result sets: ensure virtualization or server pagination and add a UI message to refine selection.

---

## Timeline (estimates)
- Research & design: 1–2 days (done: research.md)
- Backend: 2–3 days
- Frontend: 3–4 days
- Integration, accessibility & performance testing: 1–2 days
- Total: ~7–11 working days (iterative commits + small PRs recommended)

---

## Next actions (immediate)
1. Add contract files (create `contracts/build-items.json` and `contracts/items-lookup.json`).
2. Implement shared fuzzy util and tests (backend).
3. Implement `GET /items/lookup` and `GET /builds/items` (backend + tests).
4. Implement frontend selection panel and item-table UI (templates, HTMX endpoints if server-driven updates used).
5. Add Playwright smoke tests for the primary user flows.

---

## References
- Spec: `specs/002-frontend-ui-redesign/spec.md`
- Data model: `specs/001-design-a-frontend/data-model.md`
- Contract example: `specs/001-design-a-frontend/contracts/variant.json`
- Existing fuzzy algorithm: `frontend/src/services/filtering.py::fuzzy_score`
