# Diablo 3 Build Guide Item Scraper – API Implementation Plan

**Status Note (July 2025):**
The API module described here is planned but not yet implemented. This document supersedes any API-related planning or claims in `databaseImplementation.md`. For current database and query logic, see `databaseImplementation.md` and the data module. The API will depend on the data/query layer for all backend access. Separation of concerns between data and API modules is intentional and future milestones will be tracked here.

## Overview

This document outlines the API design, endpoints, and integration considerations for serving Diablo 3 build guide data to a web UI or other clients. The API is implemented as a separate module, decoupled from the database logic for maintainability and scalability.

---

## API Technology Choices

- **Framework:** FastAPI (Python)
- **Data Format:** JSON (for all responses)
- **CORS:** Enabled for frontend access
- **Documentation:** OpenAPI auto-generated docs
- **Testing:** pytest

---

## Directory Structure

```directory
src/
  d3_item_salvager/
    api/
      main.py         # FastAPI app and endpoint registration
      endpoints.py    # Endpoint implementations
      schemas.py      # Pydantic models for request/response
      dependencies.py # Dependency injection (DB session, etc.)
    ...
tests/
  api/
    test_endpoints.py # Unit tests for API endpoints
    ...
docs/
  apiImplementation.md  # This design document
```

---

## API Endpoints

- **GET /items** – List items, filter by class, slot, set_status, usage_context, supports pagination
- **GET /builds** – List builds
- **GET /profiles** – List profiles, filter by class/build
- **GET /item_usages** – List item usages, filter by profile, item, usage_context

### Filtering & Query Parameters

- All endpoints support query parameters for filtering (e.g., class_name, slot, set_status, usage_context)
- Pagination via `limit` and `offset` parameters

### Response Format

- All responses are JSON, structured according to Pydantic schemas
- Error responses use standard HTTP status codes and JSON error objects

---

## Integration Considerations

- CORS enabled for frontend web UI
- Endpoints designed for fast queries and grouping/filtering as needed by the UI
- OpenAPI docs for easy client integration and testing
- API is decoupled from database logic; can swap backend if needed

---

## Authentication & Security (Future)

- Add authentication (API keys, OAuth) if needed for user-specific features
- Rate limiting and monitoring for production deployments

---

## Testing

- Unit tests for all endpoint logic and error handling
- Use pytest and coverage tools

---

## Summary

This API implementation plan provides a clear, maintainable foundation for serving Diablo 3 build guide data to web and other clients. The design supports rapid iteration, robust filtering, and future extensibility.

---

## Implementation Notes (October 2025)

- Initial endpoints (`/items`, `/builds`, `/profiles`, `/item_usages`) are implemented and return payloads in the form `{ "data": [...], "meta": { "limit", "offset", "total" } }` to surface pagination details alongside results.
- CORS is currently configured to allow all origins to simplify local development; the configuration can be tightened via future `ApiConfig` settings once frontend requirements are finalized.
