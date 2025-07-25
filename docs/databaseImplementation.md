# Diablo 3 Build Guide Item Scraper – Database Implementation Plan

## Overview

This document outlines the database design, tooling, and workflow for storing, querying, and serving scraped Diablo 3 build guide data. The goal is to enable fast, flexible queries and seamless API access for a web UI.

---

## Library and Tooling Choices

- **Database:** SQLite (local development/prototyping), with option to migrate to PostgreSQL/MySQL for scale
- **ORM:** SQLAlchemy (Python)
- **API:** FastAPI (Python)
- **Scraping:** requests/cloudscraper, BeautifulSoup
- **Testing:** pytest
- **Migrations:** Alembic (optional, for schema evolution)

---

## Directory Structure

```
src/
  d3_item_salvager/
    data/
      models.py        # SQLAlchemy models (Build, Profile, Item, ItemUsage)
      db.py            # Database engine/session setup
      loader.py        # Functions to insert scraped data
      api.py           # FastAPI endpoints for querying data
    ...
tests/
  data/
    test_loader.py     # Unit tests for loader functions
    test_api.py        # Unit tests for API endpoints
    ...
docs/
  databaseImplementation.md  # This design document
```

---

## Database Schema

### Tables

- **Build**
  - id (PK)
  - title
  - url

- **Profile**
  - id (PK)
  - build_id (FK to Build)
  - name (variant/profile name)
  - class_name

- **Item**
  - id (PK, from master item list)
  - name
  - image_url
  - slot
  - set_status
  - notes

- **ItemUsage**
  - id (PK)
  - profile_id (FK to Profile)
  - item_id (FK to Item)
  - usage_context (main, follower, kanai)

### Relationships

- Build has many Profiles
- Profile has many ItemUsages
- ItemUsages links to Items

### Indexes

- On class_name, usage_context, slot for fast queries

---

## API Endpoints (FastAPI)

- **/items** – List items, filter by class, slot, set_status, usage_context
- **/builds** – List builds
- **/profiles** – List profiles, filter by class/build
- **/item_usages** – List item usages, filter by profile, item, usage_context

All endpoints return JSON for easy web UI integration. Support pagination and CORS for frontend access. OpenAPI docs auto-generated for testing.

---

## Workflow

1. Scrape build guides and profiles
2. Parse and normalize data
3. Insert into database using loader functions
4. Serve data via FastAPI endpoints
5. Connect frontend to API for queries and display

---

## Migration and Versioning

- Use Alembic for schema migrations if needed
- Document schema changes and provide migration scripts

---

## Testing

- Unit tests for loader functions, API endpoints, and query logic
- Use pytest and coverage tools

---

## Key Functions

- `create_db()` – Initialize database and tables
- `insert_build(title, url)`
- `insert_profile(build_id, name, class_name)`
- `insert_item(id, name, image_url, slot, set_status, notes)`
- `insert_item_usage(profile_id, item_id, usage_context)`
- `query_items(...)` – Flexible query logic for API
- API endpoints for filtered queries

---

## Considerations for API/Web Integration

- Ensure all queries are fast and support filtering/grouping as needed by the frontend
- Return data in JSON format
- Support CORS for frontend access
- Document endpoints with OpenAPI
- Plan for future migration to scalable DB if needed

---

## Summary

This plan provides a robust, extensible foundation for storing, querying, and serving Diablo 3 build guide data. The schema and tooling choices support rapid iteration, easy API access, and future scalability.
