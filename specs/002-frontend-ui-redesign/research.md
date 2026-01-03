# research.md — Frontend UI Redesign

## Findings (Phase 0)

1. Fuzzy matching implementation exists in the repo:
   - File: `frontend/src/services/filtering.py`
   - Function: `fuzzy_score(candidate: str, query: str) -> int`
   - Behavior: prefix & substring matches score highly; subsequence matches allowed with penalties; returns integer scores. Unit tests exist in `frontend/tests/unit/test_filtering.py`.

2. Existing backend endpoints and queries relevant to feature:
   - `GET /variants/{variant_id}` and `GET /item-usage/{variant_id}` return item usage and nested item metadata (see `src/d3_item_salvager/api/endpoints.py`).
   - `data/queries.py` provides `get_items_by_build`, `get_items_for_profile`, and `list_items` which can be used or composed to return build-specific item lists.

3. Contract baseline:
   - `specs/001-design-a-frontend/contracts/variant.json` contains `ItemUsage` and `Variant` schemas we can reuse for item metadata.

## Decisions & Recommendations

- Reuse existing `fuzzy_score` logic to avoid UX divergence. Move or copy an adapted, well-tested implementation into the backend under `d3_item_salvager.utility.search` so both frontend and backend use the same logic.
- Prefer to add additive endpoints: `GET /builds/items` (supports multiple build ids) and `GET /items/lookup` (search/validate). These keep frontend work simple and maintain API contract clarity.
- Keep behavior conservative: suggestions should be limited (e.g., top 3), and fuzzy thresholds should be tested with unit tests.

## Open Questions (resolved during scoping)
- Q1: Selection UI pattern — chosen: Inline collapsible panel (A).
- Q2: Fuzzy behavior — chosen: reuse existing project fuzzy-matching implementation (conservative defaults).
- Q3: Multi-class selection — chosen: Allow multiple classes (B).

## Next steps from research
- Add contract files for the two endpoints.
- Implement backend shared fuzzy util and endpoints with tests.
- Implement frontend UI using HTMX/Jinja2 and wire to endpoints.
