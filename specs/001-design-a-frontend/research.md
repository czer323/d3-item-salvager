# research.md

## Purpose

Resolve open decisions from the implementation plan for the `001-design-a-frontend` feature.

## Open questions and decisions

### 1) CLI/API contract / JSON-mode test endpoint

Decision: Provide a small, optional JSON-mode endpoint in the frontend for automated tests (HTMX flows will remain primary).

Rationale: The repository constitution requires clear contracts for user-facing features. While the frontend is primarily server-rendered via HTMX and Jinja2, adding a lightweight JSON-mode endpoint (for example `/variant/{id}.json` returning variant+items+usage) simplifies automated smoke tests and CI checks without changing backend contracts. This endpoint can be implemented as a thin wrapper that calls existing backend endpoints and returns a single JSON object.

Alternatives considered:

- Do nothing and have tests interact with HTML only (slower and more brittle for verification).
- Extend backend API (not desired for MVP).

Impact: Minor additional routes in the frontend app; no backend changes required.

### 2) Headless integration test runner: Playwright vs Selenium

Decision: Use Playwright for headless integration/smoke tests.

Rationale: Playwright provides fast, modern browser automation with built-in support for multiple browsers, network interception, and a nice Python binding. It supports headless runs in CI and is well-suited for end-to-end and smoke tests. Playwright tests are typically faster and less flaky than Selenium for modern web apps.

Alternatives considered:

- Selenium: mature but heavier and often more fragile; requires managing browser drivers.

Impact: Add `playwright` as a dev/test dependency and include a small test harness under `frontend/tests/`.

### 3) Tailwind CSS setup: CDN vs Local build

Decision: Start with CDN-based Tailwind (for MVP prototypes) and add a local build (PostCSS + Tailwind CLI) if we need customizations or size optimization.

Rationale: CDN-based Tailwind/DaisyUI speeds development and reduces build complexity for an internal MVP. If styles need purging or custom plugins, switch to a local Tailwind build and include the build step in the frontend's minimal pipeline.

Alternatives considered:

- Local Tailwind build from the start: more configuration and requires Node-based tooling.

Impact: Use CDN for the initial templates in `/frontend/templates/`; document the migration path to a local build in `README.md`.

### 4) Client-side performance: list virtualization

Decision: Implement server-side pagination and HTMX-driven partial views for long lists, and lightweight client-side virtualization only if profiling shows need.

Rationale: HTMX works well with server-paginated partials; this keeps the frontend simple and avoids adding heavy client-side libraries. For very long lists, implement simple server-side pagination/virtualization via incremental HTMX requests (e.g., load more, or windowed partials). If a richer client-side virtualization is demanded later, consider `virtual-scroller` small libraries.

Alternatives considered:

- Always ship client-side virtualization library (adds JS weight and complexity).

## Conclusion

All open questions resolved for Phase 0. Next: generate `data-model.md`, API contracts and quickstart for running the frontend prototype.
