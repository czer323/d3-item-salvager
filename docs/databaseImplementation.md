# Diablo 3 Build Guide Item Scraper – Database Implementation Plan

## Overview

This document outlines the database design, tooling, and workflow for storing, querying, and serving scraped Diablo 3 build guide data. The goal is to enable fast, flexible queries and seamless API access for a web UI.

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
- Always import all models before calling SQLModel.metadata.create_all(engine).
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
      api.py           # FastAPI endpoints for querying data (should use queries.py for DB access)
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

All models are defined in `models.py` with type annotations and Field for PKs, FKs, and indexes. This structure supports flexible queries and future extensibility.

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

# Note: Continue reviewing other item objects in the data to confirm attribute naming consistency (e.g., 'type' vs 'slot').

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

- On profile_id, item_id, slot, usage_context for fast queries

**Extensibility:**

- If user-specific data is needed, add a separate table for user preferences.
- ItemUsage can be extended with more fields (e.g., notes, stat overrides) if needed.

**Best practice:**

- Loader functions insert into Item (from master data), Build/Profile (from scraped guides), and ItemUsage (from profile item lists).
- Query logic uses joins to get item names and metadata for each profile/build.

---

## Workflow

1. Scrape build guides and profiles
2. Parse and normalize data
3. Insert into database using loader functions (use Session(engine) and SQLModel models)
4. Query and analyze data for downstream use (API, web UI, etc.)

## Migration and Versioning

- Use Alembic for schema migrations if needed
- Document schema changes and provide migration scripts

---

## Testing

- Use a separate SQLite database for tests (e.g., sqlite:///testing.db)
- Create tables at test startup, clean up after tests
- Unit tests for loader functions and query logic (API endpoints tested separately)
- Use pytest and coverage tools
- **Windows-specific note:** When using SQLite for tests, always call `engine.dispose()` before deleting the database file in test teardown to avoid file locking errors. This ensures all connections are closed and the file can be removed cleanly.

---

## Key Functions

- `create_db_and_tables()` – Initialize database and tables
- `insert_build(title, url)`
- `insert_profile(build_id, name, class_name)`
- `insert_item(id, name, type, set_status, notes)`
- `insert_item_usage(profile_id, item_id, usage_context)`
- `query_items(...)` – Flexible query logic for downstream use

---

## Considerations for API/Web Integration

- Ensure all queries are fast and support filtering/grouping as needed by the frontend or API
- Use SQLModel's select, offset, limit, and index features for efficient queries
- Plan for future migration to scalable DB if needed

---

## Step-by-Step Implementation Plan

Here’s the most logical step-by-step approach for implementation:

1. **Set up the project environment and database schema**
   - Create models.py with Build, Profile, Item, and ItemUsage classes.
   - Write a script to initialize the SQLite database.

2. **Implement basic loader and query functions**
   - Insert sample data (hardcoded items, builds, profiles, usages).
   - Add simple queries to fetch items and usage contexts, validating relationships.

3. **Expand loader to handle real data**
   - Parse and insert data from reference data.json and sample build/profile JSONs.
   - Validate relationships and lookups with real data.
   - Add error handling and data validation.

4. **Implement query/filter logic**
   - Support filtering by class, build, slot, usage context, etc.
   - Test queries for correctness and performance.
   - Add unit tests for loader and query logic.

5. **Build API layer with FastAPI**
   - Expose endpoints for querying items, builds, profiles, and usages.
   - Support filtering/grouping for frontend needs.
   - Test API endpoints.

6. **Develop web UI or CLI**
   - Start with a minimal interface for displaying items and usage contexts.
   - Iterate to add filtering, grouping, and user preference features.
   - Test UI with real data and API.

7. **Finalize migration/versioning, documentation, and testing**
   - Add Alembic support for schema migrations.
   - Document usage, configuration, and extensibility.
   - Perform end-to-end testing and review for performance and maintainability.

This incremental approach ensures you build a solid foundation and can iterate quickly toward the final product.

---

## Function Responsibilities and Best Practices

- **models.py**: SQLModel class definitions (tables, relationships)
- **db.py**: Engine/session setup, model imports (ensures tables are registered)
- **loader.py**: Data ingestion, ETL, insert/bulk load functions only
- **queries.py**: Query/filter logic, reusable select/filter functions, business rules
- **api.py**: FastAPI endpoints, should use queries.py for DB access

**Best practice:**

- Keep ingestion (loader) and query/filter logic (queries) separate.
- Centralize engine and model imports in db.py for table registration.
- Use relative imports within the package for maintainability.
- Structure code so that query/filter logic is reusable for API, CLI, and tests.
