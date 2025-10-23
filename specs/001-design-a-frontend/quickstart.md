# quickstart.md

This file describes how to run the frontend prototype for the `001-design-a-frontend` feature.

## Overview

The frontend is a minimal HTMX/Jinja2 app living under `/frontend` (not yet created). It talks to the existing FastAPI backend endpoints to list build guides, variants and variant items. For automated tests we expose an optional JSON-mode endpoint under `/frontend/variant/{id}.json` which aggregates variant data for assertions.

## Local dev (MVP)

1. Start the FastAPI backend as you normally would (see repository README).
2. In a new terminal, run: `cd frontend && flask --app app run --port 8001`
3. Open <http://localhost:8001/> (or the port the frontend uses) and navigate the UI.

Notes:

- Tailwind is included via CDN for MVP; switch to a local build if customization or purging is required.
- Playwright is the recommended test runner for headless smoke tests; see `frontend/tests/`.
