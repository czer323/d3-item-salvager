# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Status**: Draft
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quick class & build selection (Priority: P1)

A user who has not yet selected any classes or builds arrives at the page and needs to quickly select one or more classes and associated builds.

**Why this priority**: This is the primary entry point for almost all workflows: users must be able to choose the class+build set before they can view and manage items.

**Independent Test**: Start with a fresh session (no classes or builds selected). The selection panel is visible and the user can pick one or more classes and one or more builds in < 10 seconds using keyboard or mouse.

**Acceptance Scenarios**:

1. Given no classes or builds are selected and no search has been run, When the user opens the page, Then a compact selection UI is visible that allows quick selection of one or more classes and their builds.
2. Given the user has selected at least one build, When the selection is complete, Then the selection UI collapses into a compact summary bar and the item list populates.
3. Given the selection is collapsed, When the user clicks the summary or "Edit" affordance, Then the full selection UI expands again and allows modifications.

---

### User Story 2 - Item list populates by selected build (Priority: P1)

After selecting class and build(s), the item list must show every item required by the selected build(s), with no reliance on the free-text search to populate the list.

**Why this priority**: Users expect to see the full list for a build so they can validate and act on all required items.

**Independent Test**: With a known build selected, verify the item list contains every canonical item referenced by that build.

**Acceptance Scenarios**:

1. Given build X is selected, When the page renders, Then the list shows all items required by build X sorted alphabetically by item name.
2. Given multiple builds are selected, When the page renders, Then the list shows the union of all required items (no duplicates), sorted alphabetically.

---

### User Story 3 - Search validates against the full DB and indicates salvageables (Priority: P1)

A user may type an item name in the search field to confirm presence in the selected build(s). Searches must match against the canonical database, tolerate minor misspellings (see clarifications), and clearly indicate whether a found item is part of the current selection or is salvageable if not present.

**Why this priority**: Users sometimes type item names to check or confirm; mis-typing should not cause false positives/negatives.

**Independent Test**: Using controlled inputs (correct name, misspelled name, unknown name), verify that search returns: the canonical match if exists (and whether it appears in the current list), suggestions if fuzzy match finds close alternatives, or a clear "salvageable" indication when no match is found.

**Acceptance Scenarios**:

1. Given user types an exact canonical item name that is in selected builds, Then the UI highlights it in the list.
2. Given user types a name that differs by a small typo, Then the system suggests the closest canonical match and shows whether it is in the current list or salvageable.
3. Given user types a name with no reasonable match in DB, Then the UI indicates this item is not in DB and can be marked salvageable.

---

### User Story 4 - Item table clarity & filtering (Priority: P1)

Users need a clear table view: Name (color-coded set/legendary), Class column (single or multi-valued), Usage multi-values (main/follower/kanai). They should be able to sort and filter by name and by usage. The number-of-variants column is removed.

**Why this priority**: Table clarity reduces cognitive load and supports the primary task of deciding what to keep vs salvage.

**Independent Test**: With sample data, verify colors appear for set (green) and legendary (orange); class column shows one or more class names depending on usage; usage shows one or more of {main, kanai, follower}; name column sorts alphabetically; usage column can be filtered to show/hide items by usage type.

**Acceptance Scenarios**:

1. Given item is a set piece, When displayed, Then its name is styled green and an ARIA label indicates "set item".
2. Given item is legendary, When displayed, Then ARIA label indicates "legendary".
3. Given user clicks the name column header, When clicked, Then the list toggles between ascending/descending alphabetical order.
4. Given user filters usage to show only "main", When applied, Then items that are only used on follower/kanai are hidden.

---

### Edge Cases

- No items returned for selected builds (empty list) — UI shows a friendly message and an action to "Check builds or clear selection".
- Very large builds (hundreds of items) — table must be paginated or virtualized to maintain performance (non-functional requirement).
- Multiple items with identical display names — show unique identifier / tooltip (unique item name) to disambiguate.
- Accessibility: color alone must not be the only cue for set/legendary; include ARIA labels and (optionally) small icon glyphs.
- Search input produces many fuzzy suggestions — cap suggestions and offer “no match - salvageable” option.

<!-- INSERT: NFR MEASUREMENT CLARIFICATIONS - BEGIN -->
**Measurement (NFR-001 & NFR-003).** For clarity and repeatability, the project defines the measurement method and thresholds here: measure **Initial Render** (NFR-001) as client-side time-to-interactive (TTI) captured via Playwright navigation timing (use the navigation entry's `domInteractive` or Playwright trace-derived TTI) in the Playwright lab using the standard lab network profile (RTT 50ms, 5 Mbps down, 1 Mbps up). Acceptance: **median TTI ≤ 300 ms** across 30 CI lab runs; report median and 95th percentile. Measure **Search Suggestions latency** (NFR-003) as client-side elapsed time from user keystroke to DOM update that renders suggestions (use Playwright marks or telemetry). Acceptance: **median ≤ 200 ms** across 30 lab runs; report median and 95th percentile. Instrument the items lookup API server-side to report request latencies (median & 95th) for correlation and investigation.
<!-- INSERT: NFR MEASUREMENT CLARIFICATIONS - END -->

<!-- INSERT: FUZZY MATCH THRESHOLDS - BEGIN -->
**Clarification (FR-004 — fuzzy thresholds & canonical tests).** Define deterministic thresholds and example cases to make acceptance tests precise and automatable. Use the canonical scoring function (`frontend/src/services/filtering.py::fuzzy_score`) as the source of truth for scoring.

Rules (apply score normalization across lengths):
- **Exact match:** score >= **0.95** -> match
- **Single-character typo** (Levenshtein distance = 1): score >= **0.80** -> match
- **Adjacent swap (transposition):** score >= **0.78** -> match
- **Missing single character:** score >= **0.75** -> match
- **Long-word relaxed (length ≥ 9):** allow up to **2 edits** if score >= **0.60** -> match
- **No match:** score < **0.50** -> no match

Example test cases (unit tests should assert both boolean match outcome and score ranges):
1. Exact match: `query="sword"` vs. candidate `"sword"` — expect **match**, score ≥ 0.95
2. Single-char missing: `query="sord"` vs. candidate `"sword"` — expect **match**, score ≥ 0.75
3. Adjacent swap: `query="sowrd"` vs. candidate `"sword"` — expect **match**, score ≥ 0.78
4. Single-char typo: `query="sward"` vs. candidate `"sword"` — expect **match**, score ≥ 0.80
5. Long-word 2 edits: `query="exraordinary"` vs. candidate `"extraordinarily"` — expect **match**, score ≥ 0.60
6. No match: `query="iron"` vs. candidate `"banana"` — expect **no match**, score < 0.50

Tests for these cases must be added to `tests/unit/filtering/test_fuzzy_thresholds.py` and must be written **test-first** (failing before code changes). Implementations must reference or align with the canonical `fuzzy_score` implementation noted below.
<!-- INSERT: FUZZY MATCH THRESHOLDS - END -->

<!-- INSERT: SELECTION PERSISTENCE - BEGIN -->
**Selection persistence (MUST).** Selection state **MUST** persist across full page reloads and soft navigations. Acceptance tests (integration):
- Given selected items, when the page is reloaded, the same items must be restored and visibly selected within **200 ms** of the page reporting TTI.
- Given selected items, after a transient network loss and reconnection, selection must reappear automatically when the UI becomes interactive.
- Tests must cover both anonymous (client-side localStorage) and authenticated (server-side persistence + client restore) flows where applicable.

**Deterministic collapse trigger.** The selection UI **must** collapse only when the user explicitly finalizes selection — **either** by clicking **Apply** **or** by pressing **Enter** while the selection UI is focused. Clicking outside must **not** collapse the selection UI unless that click is an Apply-equivalent action. Add an acceptance test: selecting items and pressing Enter or clicking Apply collapses the selection UI deterministically.
<!-- INSERT: SELECTION PERSISTENCE - END -->

---

*Canonical implementation reference:* `frontend/src/services/filtering.py::fuzzy_score`

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present a **compact, quick-selection UI** for class(es) and build(s) when the user has no builds selected or has not yet run a search, and MUST allow selecting multiple classes and builds simultaneously.
- **FR-002**: The selection UI MUST collapse into a compact summary (showing selected class/builds) after a build is selected or after the initial search is run, and MUST be expandable on user demand.
- **FR-003**: The system MUST populate the item list with the union of all items required by the selected class(es) and build(s) immediately after selection, without requiring additional search input.
- **FR-004**: The search field MUST validate typed names against the canonical item database and return canonical matches, fuzzy suggestions for small typos, or indicate "salvageable" when no DB match exists. The project’s existing fuzzy-matching implementation should be reviewed and leveraged where possible; if insufficient, extend conservatively with tests.
- **FR-005**: The item table MUST include columns: **Name**, **Class**, **Usage** (multi-valued). Name texts MUST be color-coded (green for set items, orange for legendary items) based on the item's `quality` field (string: `'set'` | `'legendary'`). Color MUST be accompanied by non-color cues (icon + ARIA label) for accessibility.
- **FR-006**: The item table MUST NOT display the variants count column.
- **FR-007**: The item table MUST be sorted alphabetically by default and allow toggling ascending/descending by clicking the Name column header.
- **FR-008**: The table MUST provide filter controls for Usage types (main/follower/kanai) to allow showing only selected usage types.
- **FR-009**: When a user types in search and a matching canonical item exists but is not part of current selection, the UI MUST clearly indicate it is not in the selected build(s) and provide an affordance to add it to the current selection or mark it salvageable.
- **FR-010**: All interactions MUST be keyboard navigable and comply with basic accessibility (WCAG 2.1 AA for color contrast and focus management).

### Non-Functional Requirements

- **NFR-001**: Initial load with selection collapsed must render within 300ms on typical desktop connections.
- **NFR-002**: Item lists of up to 1000 entries must remain responsive; use virtualization or server-side pagination.
- **NFR-003**: Search fuzziness must be fast enough to return suggestions within 200ms for typical queries.

### Key Entities

- **Class**: e.g., Barbarian, Wizard — used to scope builds
- **Build**: Named configuration that lists required items
- **Item**: Canonical game item record with attributes: canonical_name, unique_name, slot, quality (string; one of `'set'` or `'legendary'` — mutually exclusive), usages(list of {main, kanai, follower})
- **SelectionState**: represents user's current class(s) and build(s)
- **SearchResult**: {match_type: exact|fuzzy|none, item?: Item, suggestions?: [Item], salvageable?: bool}

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of target users can select class+build and collapse the selection within 10 seconds on first attempt (measured in user test session of N=10).
- **SC-002**: Search correctly identifies canonical matches or reasonable fuzzy suggestions in ≥95% of scripted test cases (unit/integration tests using a variety of typos and synonyms).
- **SC-003**: Default alphabetical sorting applied and toggles correctly in 100% of UI tests.
- **SC-004**: Filtering by usage hides/shows correct items in 100% of deterministic tests.
- **SC-005**: Accessibility checks (color contrast, ARIA labels, keyboard navigation) must pass automated accessibility tests for the new screens.

## Assumptions

- Builds and their item lists are stored server-side and an API endpoint exists to fetch all items for a build.
- Canonical item database is authoritative for matches and suggestion generation.
- Color-coding (green/orange) is acceptable but must have non-color cues for accessibility.
- The repository already contains a fuzzy-matching implementation at `frontend/src/services/filtering.py` (`fuzzy_score`) which will be reviewed and reused or moved into a shared utility for server-side use.
- Selection state (chosen classes/builds) **MUST** persist across page reloads using browser `localStorage` (or server-side persistence for authenticated sessions), so the collapsed/expanded state and recent selections survive refreshes. This requirement has been promoted from SHOULD → **MUST** and has an associated integration test (see T028).

## Clarifications

### Session 2026-01-02

- Q: Should the UI allow selecting multiple classes at once? → A: B (Allow multiple classes)

**Applied**: Selection UI and item union behavior updated to allow multiple classes; `FR-001` and `FR-003` updated; User Story acceptance scenarios updated to reference classes explicitly.


## Questions (Clarifications - max 3)

### Q1: Selection UI pattern

**Context**: The brief asks for a "more elegant" selection UI that can be hidden/collapsed and re-expanded. This could be implemented as either:

| Option | Answer | Implications |
|--------|--------|--------------|
| A | Inline collapsible panel (default) | Quick to access, occupies no extra modal overlays, simpler state to maintain. Best for fast, non-modal flows. |
| B | Slide-over / drawer or modal that opens on demand | Cleaner default page (less visible clutter), but needs additional animation and focus handling for accessibility. |
| C | Toolbar with chips (compact summary) + focused modal for editing | Summary is very compact; editing experience can be richer but adds implementation complexity. |

**Your choice**: A (Inline collapsible panel chosen).

### Q2: Search matching & fuzzy behavior

**Context**: The spec asks for tolerance for misspellings and suggestions. We need to agree on acceptable behavior.

| Option | Answer | Implications |
|--------|--------|--------------|
| A | Conservative fuzzy matching (Levenshtein distance ≤ 1 for short words, ≤2 for longer words), return top 3 suggestions | Low false positives, simple to implement, may miss some typos. |
| B | More aggressive fuzzy matching + "Did you mean" suggestions using tokenized matching and synonyms, return top 5 | Better UX for typos but risk of false positives and increased compute cost. |
| C | No fuzzy matching; exact canonical match only; provide spell-check suggestions via server-side lookup if no match | Simplest to reason about but less forgiving of typos. |

**Your choice**: Use existing project fuzzy-matching implementation; review and reuse/extend as needed (conservative defaults).


---

If these clarifications are provided, the spec will be updated and validated against the checklist.

---

*Prepared for planning & estimation.*
