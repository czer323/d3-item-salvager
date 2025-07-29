# Diablo 3 Build Guide Item Scraper – Database Implementation Plan

This document defines the requirements and expectations for the database and query/data layer. API implementation is specified in `apiImplementation.md`, which supersedes any API-related planning here. Separation of concerns between data and API modules is required; API and web UI are tracked in their respective documents.

## Overview

The database and data layer must store, query, and serve scraped Diablo 3 build guide data. The design enables fast, flexible queries and seamless API access for a web UI.

---

## Library and Tooling Choices

- **Database:** SQLite (local development/prototyping), with option to migrate to PostgreSQL/MySQL for scale
- **ORM:** SQLModel (Python, built on SQLAlchemy and Pydantic)
- **API:** FastAPI (Python)
- **Scraping:** requests/cloudscraper, BeautifulSoup
- **Testing:** pytest
- **Migrations:** Alembic (optional, for schema evolution)

**Best Practices:**

- Use SQLModel for all model definitions, with type annotations and Field for PKs, indexes, defaults, and FKs.
- Import all models before calling SQLModel.metadata.create_all(engine).
- Use context-managed Session(engine) for all DB operations.
- Use Field(index=True) for indexed columns.
- Use Field(foreign_key="tablename.column") for relationships.

---

## Directory Structure

```directory
src/
  d3_item_salvager/
    data/
      models.py        # SQLModel models (Build, Profile, Item, ItemUsage)
      db.py            # Database engine/session setup
      loader.py        # Functions to insert scraped data (ingestion/ETL only)
      queries.py       # Query/filter logic (filter by class, build, slot, usage context, etc.)
      api.py           # FastAPI endpoints for querying data (specified in apiImplementation.md)
    ...
tests/
  data/
    test_loader.py     # Unit tests for loader functions
    test_queries.py    # Unit tests for query/filter logic
    test_api.py        # Unit tests for API endpoints
    ...
docs/
  databaseImplementation.md  # This design document
```

---

## Database Schema

### Model Definitions (SQLModel)

All models are defined in `models.py` with type annotations and Field for PKs, FKs, and indexes. This structure supports flexible queries and extensibility.

```python
from typing import Optional
from sqlmodel import SQLModel, Field

class Build(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str

class Profile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    build_id: int = Field(foreign_key="build.id")
    name: str
    class_name: str = Field(index=True)

class Item(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    type: str  # Note: 'type' directly correlates to the 'slot' concept in builds and item usage.
    quality: str


# Item objects must use consistent attribute naming (e.g., 'type' vs 'slot').

class ItemUsage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profile.id", index=True)
    item_id: int = Field(foreign_key="item.id", index=True)
    slot: str = Field(index=True)
    usage_context: str = Field(index=True)
```

**Schema summary:**

- `Item`: Master list of all items, with full metadata. Used for all lookups and display.
- `Build`: Represents each build/guide.
- `Profile`: Variant of a build, links to Build.
- `ItemUsage`: Join table linking Profile to Item, with slot and usage_context (main, follower, kanai). Each profile can have its own set of item usages.

**Relationships:**

- Build has many Profiles
- Profile has many ItemUsages
- ItemUsages links to Items

**Indexes:**

- Indexes on profile_id, item_id, slot, usage_context for fast queries

**Extensibility:**

- User-specific data is supported by adding a separate table for user preferences.
- ItemUsage can be extended with additional fields (e.g., notes, stat overrides).

**Best practice:**

- Loader functions insert into Item (from master data), Build/Profile (from scraped guides), and ItemUsage (from profile item lists).
- Query logic uses joins to get item names and metadata for each profile/build.

---

## Workflow

1. Scrape build guides and profiles
2. Parse and normalize data
3. Insert into database using loader functions (use Session(engine) and SQLModel models)
4. Query and analyze data for downstream use (API and web UI are specified in `apiImplementation.md`)

## Migration and Versioning

- Alembic is used for schema migrations.
- Schema changes and migration scripts are documented as the project evolves.

---

## Testing

- Use a separate SQLite database for tests (e.g., sqlite:///testing.db)
- Create tables at test startup, clean up after tests
- Unit tests for loader functions and query logic
- API endpoint tests are specified in `apiImplementation.md`
- Use pytest and coverage tools
- **Windows-specific note:** When using SQLite for tests, always call `engine.dispose()` before deleting the database file in test teardown to avoid file locking errors. This ensures all connections are closed and the file can be removed cleanly.

---

## Key Functions

- `create_db_and_tables()` – Initializes database and tables
- `insert_build(title, url)`
- `insert_profile(build_id, name, class_name)`
- `insert_item(id, name, type)`  # set_status and notes are not required
- `insert_item_usage(profile_id, item_id, usage_context)` # item_id must match Item.id type
- `query_items(...)` – Flexible query logic for downstream use

---

## Considerations for API/Web Integration

- API and web integration are specified in `apiImplementation.md`.
- Queries must be fast and support filtering/grouping for API/frontend needs.
- Use SQLModel's select, offset, limit, and index features for efficient queries.
- Migration to a scalable DB is supported.

---

## Step-by-Step Implementation Plan

1. **Set up the project environment and database schema**
   - Create models.py with Build, Profile, Item, and ItemUsage classes.
   - Write a script to initialize the SQLite database.

2. **Implement loader and query functions**
   - Insert sample data (hardcoded items, builds, profiles, usages).
   - Add queries to fetch items and usage contexts, validating relationships.

3. **Expand loader to handle real data**
   - Parse and insert data from reference data.json and sample build/profile JSONs.
   - Validate relationships and lookups with real data.
   - Add error handling and data validation.

4. **Implement query/filter logic**
   - Support filtering by class, build, slot, usage context, etc.
   - Add unit tests for loader and query logic.

5. **API layer with FastAPI**
   - Specified in `apiImplementation.md`.

6. **Web UI or CLI**
   - Specified in frontend documentation.

7. **Migration/versioning, documentation, and testing**
   - Alembic support and documentation required.
   - End-to-end testing and review for performance and maintainability required.

---

## Function Responsibilities and Best Practices

- **models.py**: SQLModel class definitions (tables, relationships)
- **db.py**: Engine/session setup, model imports (ensures tables are registered)
- **loader.py**: Data ingestion, ETL, insert/bulk load functions only
- **queries.py**: Query/filter logic, reusable select/filter functions, business rules
- **api.py**: API endpoints specified in `apiImplementation.md`

**Best practice:**

- Keep ingestion (loader) and query/filter logic (queries) separate.
- Centralize engine and model imports in db.py for table registration.
- Use relative imports within the package for maintainability.
- Structure code so that query/filter logic is reusable for API, CLI, and tests.

---

## Schema and Data Layer Requirements

- Item model primary key is `str` (not `int`) for item uniqueness; this must be documented in API/data schemas.
- ItemUsage.item_id type must match Item.id type (`str`).
- set_status and notes fields are not required in Item model or insert function.

## API and Integration Requirements

- API endpoints and integration are specified in `apiImplementation.md`.

## Migration and Extensibility Requirements

- Alembic is required for migrations.
- End-to-end testing and review for performance and maintainability are required.
