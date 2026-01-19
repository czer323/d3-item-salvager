Playwright e2e tests

Quick start:

1. Install node deps:
   npm install

2. Install Playwright browsers:
   npx playwright install
   or: npm run playwright:install

3. Start the backend + frontend dev server (must be available at http://127.0.0.1:8001 or set FRONTEND_BASE_URL):
   uv run python -m d3_item_salvager api

4. Run e2e tests:
   npm run test:e2e

Notes:
- Tests live in `src/tests/playwright` and conform to the `*.spec.ts` naming convention.
- Playwright config is at `src/tests/playwright/playwright.config.ts`.
