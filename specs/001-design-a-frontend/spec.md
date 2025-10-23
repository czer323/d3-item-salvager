
# Feature Specification: Design a frontend application for d3-item-salvager

**Feature Branch**: `001-design-a-frontend`
**Created**: 2025-10-12
**Status**: Draft
**Input**: User description: "Design a frontend application that interfaces with the existing FastAPI backend using HTMX, Jinja2, DaisyUI and Tailwind CSS; the frontend should live in a separate application folder and provide interactive views for browsing build guides, variants, and item salvage recommendations, plus a lightweight preferences UI that stores user choices locally and supports exporting/importing preference lists."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Primary: Show build items and salvage candidates (Priority: P1)

As a user, I want the app to display all items used by the selected classes, builds and variants (sorted by item name) and separately list items that are not part of those selected builds so I can immediately see what I should keep versus what can be salvaged.

**Why this priority**: This is the core value of the product—making clear which items are required for the user's chosen builds and which are safe to salvage.

**Independent Test**: Select a set of classes/builds/variants; the UI shows a combined "Used by selected builds" list (sorted by name) and a separate "Not used / Salvage candidates" section. The counts and item names should match the sample dataset for the selected variants.

**Acceptance Scenarios**:

1. **Given** selected classes/builds/variants, **When** the user opens the variant/build summary, **Then** the UI shows a section "Used by selected builds" listing every item the selected variants require.
2. **Given** the same selection, **When** the user views the page, **Then** there is a separate, clearly labeled section "Not used / Salvage candidates" listing items not present in any selected variant.

---

### User Story 2 - Select classes, builds and variants (Priority: P1)

As a user, I want an accurate, easy-to-use selector to pick which classes, builds and variants I care about so the displayed lists (Story 1) reflect only those selections.

**Why this priority**: The selection controls drive the primary view; accurate selection is essential for correct salvage lists.

**Independent Test**: Use the selector UI to choose a class and one or more builds/variants; verify the lists in Story 1 update immediately to reflect the new selection.

**Acceptance Scenarios**:

1. **Given** the selector UI, **When** the user picks class=Barbarian and selects Build A variant 1, **Then** the item lists update to include items used by that variant only.
2. **Given** multiple selected variants, **When** the user views the summary, **Then** items used by any selected variant appear in "Used by selected builds" (duplicates should be de-duplicated and annotated with their usage contexts).

---

### User Story 3 - Save selected classes/builds/variants as preferences (Priority: P2)

As a user, I want my selected classes, builds and variants to be saved as preferences so I don't need to reselect them every time I visit the app.

**Why this priority**: Persisting the user's focus reduces friction and makes the salvage view immediately useful on return visits.

**Independent Test**: Select a set of classes/builds/variants, save preferences, reload or open the site in a new tab, and confirm the same selections are applied and the view reflects them.

**Acceptance Scenarios**:

1. **Given** a set of selected classes/builds/variants, **When** the user saves preferences, **Then** the selections persist across reloads and browser restarts.
2. **Given** exported selection preferences, **When** the user imports them, **Then** the selector UI applies the imported selections.

---

### User Story 4 - Realtime fuzzy search and slot filter (Priority: P2)

As a user, I want a search box that filters item lists in realtime with partial and fuzzy matching, plus an optional slot filter, so I can quickly locate specific items within long lists.

**Why this priority**: Fast search reduces time-to-action when users know an item name or fragment.

**Independent Test**: Type a partial item name into the search box and observe the list updating in realtime to show matching items. Apply a slot filter and confirm results narrow accordingly.

**Acceptance Scenarios**:

1. **Given** a populated item list, **When** the user types "Furnace" (or a partial sequence like "Furn"), **Then** the list filters to show matching items in realtime (supporting fuzzy/partial matches).
2. **Given** the slot filter set to "Ring", **When** the user changes the filter, **Then** the results are immediately filtered to rings. Any subsequent search terms further filter within that slot.

---

### Edge Cases

- What happens when the backend is unreachable: show an offline/error state with cached data where available and clear messaging with retry option.
- What happens when a search yields no results: display a friendly "No items found" message and suggest clearing filters or checking spelling.
- Very large builds or variants: use pagination or virtualized lists to keep UI responsive.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The frontend MUST present a browsable list of build guides grouped by class and allow opening a build to view variants.
- **FR-002**: The frontend MUST display a variant/build summary that includes two primary sections: (a) "Used by selected builds" listing every item the selected variants require (grouped by slot or sorted by name), and (b) "Not used / Salvage candidates" listing items not present in any selected variant.
- **FR-003**: The frontend MUST generate salvage candidate lists based on the currently selected classes/builds/variants and label items clearly (Keep, Salvage, Kanai, Follower) where applicable.
- **FR-004**: The frontend MUST allow users to save their selected classes, builds, and variants as preferences and persist these selections in local storage.
- **FR-005**: The frontend MUST allow export and import of selection preferences as a JSON file.
- **FR-006**: The frontend MUST provide a realtime fuzzy/partial-search box for item names and an optional slot filter; search results should filter in realtime as the user types and support partial/fuzzy matches.
- **FR-007**: The frontend MUST gracefully handle backend errors and display informative messages and retry options.
- **FR-008**: The frontend MUST be implemented using HTMX with server-rendered templates via Jinja2 and styled using Tailwind CSS + DaisyUI; interactions beyond basic HTMX flows may use minimal vanilla JS. (Tech choices per request.)
- **FR-009**: The frontend application MUST be placed in a separate folder (e.g., `/frontend`) with its own minimal project layout and independent static assets; it communicates with the existing FastAPI backend via its public endpoints.
- **FR-010**: The frontend MUST include automated UI-level smoke tests (headless integration tests) that validate the main P1 journeys (selection → used/salvage lists) and preference persistence.

*Note*: FR-008 and FR-009 specify technology choices given in the user request. The spec avoids implementation detail beyond those choices.

### Key Entities *(include if feature involves data)*

- **BuildGuide**: id, title, url, class_name, last_updated
- **Variant**: id, name, build_guide_id, list of item references
- **Item**: id, name, slot, set_status, notes
- **ItemUsage**: item_id, variant_id, usage_context (main/follower/kanai)
- **Preferences**: user selection preferences model — { selected_class_ids: list, selected_build_ids: list, selected_variant_ids: list }

## Backend Assumptions / Endpoint Contracts

### API Endpoints

The frontend assumes the following FastAPI backend endpoints are available. All endpoints return JSON responses.

#### Build Guides
- **GET /build-guides**
  - **Purpose**: List all available build guides
  - **Response**: `200 OK`
  - **Response Body**:
    ```json
    [
      {
        "id": "string",
        "title": "string",
        "url": "string",
        "class_name": "string",
        "last_updated": "string (ISO 8601 datetime)"
      }
    ]
    ```

#### Variants
- **GET /variants/{guide_id}**
  - **Purpose**: Get all variants for a specific build guide
  - **Path Parameters**: `guide_id` (string)
  - **Response**: `200 OK`
  - **Response Body**:
    ```json
    [
      {
        "id": "string",
        "name": "string",
        "build_guide_id": "string"
      }
    ]
    ```

#### Items
- **GET /items/{variant_id}**
  - **Purpose**: Get all items used in a specific variant
  - **Path Parameters**: `variant_id` (string)
  - **Response**: `200 OK`
  - **Response Body**:
    ```json
    [
      {
        "id": "string",
        "name": "string",
        "slot": "string",
        "set_status": "string",
        "notes": "string"
      }
    ]
    ```

#### Item Usage (for salvage analysis)
- **GET /item-usage/{variant_id}**
  - **Purpose**: Get detailed item usage information for salvage analysis
  - **Path Parameters**: `variant_id` (string)
  - **Response**: `200 OK`
  - **Response Body**:
    ```json
    [
      {
        "item_id": "string",
        "usage_context": "string (main/follower/kanai)",
        "item": {
          "id": "string",
          "name": "string",
          "slot": "string"
        }
      }
    ]
    ```

### Client-Side Preferences Model

For MVP, user preferences are stored as a single client-scoped object in browser localStorage under the key `"d3-item-salvager-preferences"`.

**Required Fields:**
- `selected_class_ids`: `string[]` - Array of selected Diablo 3 class IDs
- `selected_build_ids`: `string[]` - Array of selected build guide IDs
- `selected_variant_ids`: `string[]` - Array of selected variant IDs

**Optional Metadata Fields:**
- `updated_at`: `string` (ISO 8601 datetime) - Timestamp of last preference update
- `version`: `string` - Schema version for future migrations (e.g., "1.0.0")

**Example Preferences Object:**
```json
{
  "selected_class_ids": ["barbarian", "wizard"],
  "selected_build_ids": ["guide-123", "guide-456"],
  "selected_variant_ids": ["variant-789", "variant-012"],
  "updated_at": "2025-10-23T10:30:00Z",
  "version": "1.0.0"
}
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: P1 flow (select classes/builds/variants → view Used/Salvage lists) completes within 3 user actions and displays the expected content in 95% of trials during testing.
- **SC-002**: Salvage candidate lists (Used vs Not used) match the reference dataset labels for 98% of sample selections in automated tests.
- **SC-003**: Selection preferences persist across page reloads and browser restarts in 99% of cases (measured during integration tests across supported browsers).
- **SC-004**: Exported selection preference files can be imported and re-applied with 100% fidelity in automated import/export tests.
- **SC-005**: The application displays a useful error or offline state when the backend is unreachable and provides a retry control in all UI areas that request backend data.

## Assumptions

- The FastAPI backend already exposes endpoints to list build guides, fetch a single guide's variants, and fetch variant item data. If an endpoint is missing, the frontend will use available endpoints and the integration plan will document any backend additions required.
- The frontend will be shipped as a separate small project folder within the repository (e.g., `/frontend`) with its own static assets and build pipeline if needed for Tailwind processing.
- Local preference storage via browser localStorage is acceptable for MVP; backend persistence may be added later as an enhancement.
- Accessibility (a11y) requirements for MVP: WCAG 2.1 Level A minimum compliance, with Level AA targeted for color contrast. Required features include keyboard navigation, correct semantic HTML structure, visible focus states, meaningful ARIA attributes only where necessary, and proper form labeling. A full accessibility audit or remediation beyond these mandatory items is out of scope for MVP.

## Out of Scope

- Server-side rendering alternatives other than Jinja2 (e.g., SPA frameworks like React/Vue).
- Backend authentication or user accounts for persisting preferences server-side (MVP uses local storage only).
- Complex analytics, telemetry, or user tracking beyond basic logging for errors.

## Deliverables

- A new folder `/frontend` containing a minimal HTMX/Jinja2 app that can be run separately and hooked to the existing FastAPI backend.
- Example Jinja2 templates for the home page, build guide listing, variant detail, and preferences export/import UI.
- Tailwind + DaisyUI styling and simple, responsive layouts for desktop and mobile.
- Integration smoke tests that run headless and validate P1 user journeys.
- README with run instructions and notes on any backend endpoints assumed/required.

## Next Steps

1. Review this spec for scope and clarify any business decisions marked with [NEEDS CLARIFICATION] (none currently).
2. Create the frontend folder and scaffold the minimal project (templates, static, simple server) and wire to FastAPI endpoints.
3. Implement P1 user stories and the export/import preferences flow.
4. Add smoke tests and run integration checks.
5. Iterate on styling and UX based on quick user feedback.
