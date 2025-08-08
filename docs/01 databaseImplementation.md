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

## Dependency Injection and Configuration

The database layer uses a dependency injection pattern for managing database connections and configuration:

### Container Setup
```python
from d3_item_salvager.container import Container

# Application container with database engine and session factories
container = Container()
engine = container.engine()
session_factory = container.session
```

### Database Configuration
Configuration is managed through Pydantic settings with environment variable support:

```python
# Environment variables or .env file
DATABASE_URL=sqlite:///d3_items.db

# Configuration classes in config/base.py
class DatabaseConfig(BaseSettings):
    model_config = {"env_prefix": "DATABASE_"}
    url: str = "sqlite:///d3_items.db"
```

### Usage Pattern
```python
from d3_item_salvager.container import Container
from d3_item_salvager.data.loader import insert_items_from_dict
from d3_item_salvager.data.queries import get_all_items

# Initialize container
container = Container()

# Use session factory for database operations  
with container.session() as session:
    items = get_all_items(session)
    # Perform other operations
```

### Database Initialization
```bash
# Set required environment variable
export MAXROLL_BEARER_TOKEN=your_token_here

# Initialize database tables
python -m d3_item_salvager.data.init_db
```

This approach provides:
- **Centralized configuration management**
- **Testable dependency injection**
- **Environment-specific database settings**
- **Clean separation of concerns**

---

## Directory Structure

```directory
src/
  d3_item_salvager/
    data/
      models.py        # SQLModel models (Build, Profile, Item, ItemUsage) with relationships
      db.py            # Database table creation utilities
      init_db.py       # Database initialization script
      loader.py        # Functions to insert scraped data (ingestion/ETL with validation)
      queries.py       # Query/filter logic (filter by class, build, slot, usage context, etc.)
    container.py       # Dependency injection container for database engine/session management
    config/
      settings.py      # Application configuration including database settings
      base.py          # Configuration base classes
    ...
tests/
  data/
    test_loader.py     # Unit tests for loader functions
    test_queries.py    # Unit tests for query/filter logic
  fakes/
    test_db_utils.py   # Test utilities for temporary database setup
  conftest.py          # Pytest fixtures for database testing
    ...
docs/
  01 databaseImplementation.md  # This design document
  02 migrationsImplementation.md # Migration strategy (separate from core data module)
```

---

## Database Schema

### Model Definitions (SQLModel)

All models are defined in `models.py` with modern type annotations, Field for PKs, FKs, and indexes, and bidirectional Relationship mappings. This structure supports flexible queries, extensibility, and ORM-style navigation.

```python
from sqlmodel import Field, Relationship, SQLModel

class Build(SQLModel, table=True):
    """Represents a Diablo 3 build guide."""
    id: int | None = Field(default=None, primary_key=True)
    title: str
    url: str
    profiles: list["Profile"] = Relationship(back_populates="build")

class Profile(SQLModel, table=True):
    """Represents a variant/profile of a build."""
    id: int | None = Field(default=None, primary_key=True)
    build_id: int = Field(foreign_key="build.id")
    name: str
    class_name: str = Field(index=True)
    build: Build | None = Relationship(back_populates="profiles")
    usages: list["ItemUsage"] = Relationship(back_populates="profile")

class Item(SQLModel, table=True):
    """Represents an item from the master item list."""
    id: str = Field(primary_key=True)
    name: str
    type: str  # 'type' directly correlates to the 'slot' concept in builds and item usage.
    quality: str
    usages: list["ItemUsage"] = Relationship(back_populates="item")

class ItemUsage(SQLModel, table=True):
    """Represents the usage of an item in a build/profile."""
    id: int | None = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profile.id", index=True)
    item_id: str = Field(foreign_key="item.id", index=True)  # Note: str type matches Item.id
    slot: str = Field(index=True)
    usage_context: str = Field(index=True)
    profile: Profile | None = Relationship(back_populates="usages")
    item: Item | None = Relationship(back_populates="usages")
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

1. **Application Configuration**: Load database settings through the dependency injection container
2. **Database Setup**: Use the container to provide database engine and session management
3. **Table Creation**: Initialize database tables using `create_db_and_tables()` function
4. **Data Ingestion**: 
   - Scrape build guides and profiles
   - Parse and normalize data
   - Insert into database using loader functions with validation (use Session from container)
5. **Data Querying**: Query and analyze data for downstream use using the comprehensive query functions

**Dependency Injection Pattern:**
```python
from d3_item_salvager.container import Container
from sqlmodel import Session

# Initialize container
container = Container()

# Get database engine and session
engine = container.engine()
session_factory = container.session

# Use in application
with session_factory() as session:
    # Perform database operations
    pass
```

## Migration and Versioning

- Database migrations are handled separately - see `02 migrationsImplementation.md` for migration strategy
- Current implementation uses SQLModel metadata for table creation
- Schema changes should be coordinated with migration planning
- For development, database can be recreated using `init_db.py` script

---

## Testing

### Test Database Setup
- Uses temporary SQLite databases for testing via `temp_db_engine()` fixture
- Automatic table creation and cleanup for each test
- Test utilities in `tests/fakes/test_db_utils.py` provide sample data insertion helpers

### Test Structure
- **Unit tests for loader functions**: Validation, error handling, data insertion
- **Unit tests for query logic**: All query functions with various filter scenarios
- **Fixtures**: `conftest.py` provides reusable database engine fixtures
- **Sample data**: `insert_sample_data()` creates consistent test data

### Test Execution
```bash
# Run all data tests
python -m pytest tests/data/ -v

# Run with coverage
python -m pytest tests/data/ --cov=src/d3_item_salvager/data
```

### Key Test Features
- Temporary database creation with automatic cleanup
- Comprehensive validation testing (missing fields, invalid values, duplicates)
- Relationship and foreign key constraint testing
- Query result verification with sample data

---

## Key Functions

### Database Setup
- `create_db_and_tables(engine)` – Initializes database tables using SQLModel metadata

### Loader Functions (with validation)
- `insert_items_from_dict(item_dict, session)` – Insert multiple items with comprehensive validation
- `insert_build(build_id, build_title, build_url, session)` – Insert a single build record
- `insert_profiles(profiles, build_id, session)` – Insert multiple profiles for a build
- `insert_item_usages_with_validation(usages, session)` – Insert item usages with FK validation
- `validate_item_data(item_data, session)` – Validate item data before insertion

### Query Functions
- `get_all_items(session)` – Fetch all items
- `get_all_item_usages(session)` – Fetch all item usages
- `get_item_usages_with_names(session)` – Fetch usages with joined item names
- `get_items_by_class(session, class_name)` – Items used by a specific character class
- `get_items_by_build(session, build_id)` – Items used in a specific build
- `get_item_usages_by_slot(session, slot)` – Usages for a specific equipment slot
- `get_item_usages_by_context(session, usage_context)` – Usages by context (main, follower, kanai)
- `get_profiles_for_build(session, build_id)` – All profiles for a build
- `get_item_usages_for_profile(session, profile_id)` – All usages for a profile
- `get_items_for_profile(session, profile_id)` – All items used in a profile

---

## Considerations for API/Web Integration

- API and web integration are specified in `apiImplementation.md`.
- Queries must be fast and support filtering/grouping for API/frontend needs.
- Use SQLModel's select, offset, limit, and index features for efficient queries.
- Migration to a scalable DB is supported.

---

## Step-by-Step Implementation Plan

### ✅ Completed Implementation

1. **✅ Database Schema and Models**
   - Implemented models.py with Build, Profile, Item, and ItemUsage classes with full relationships
   - Set up dependency injection container for database management
   - Created database initialization script

2. **✅ Loader and Query Functions**
   - Implemented comprehensive loader functions with validation and error handling
   - Added robust query functions for all common use cases
   - Integrated foreign key validation and data integrity checks

3. **✅ Real Data Handling**
   - Loader functions handle complex validation for item types, qualities, and relationships
   - Error handling and detailed logging for data insertion operations
   - Support for bulk operations and transactional integrity

4. **✅ Query and Filter Logic**
   - Complete query implementation supporting filtering by class, build, slot, usage context
   - Type-safe SQLModel select operations with proper joins
   - Comprehensive unit test coverage for all query functions

5. **✅ Testing Infrastructure**
   - Pytest-based testing with temporary database fixtures
   - Comprehensive test coverage for loader and query logic
   - Automated test utilities for sample data generation

### 🔄 Future Enhancements

6. **API Layer Integration**
   - API endpoints are handled in separate modules as per `apiImplementation.md`
   - Database layer provides foundation for API development

7. **Advanced Migration Support**
   - Migration strategy documented in `02 migrationsImplementation.md`
   - Current approach uses metadata-based table creation for development

---

## Function Responsibilities and Best Practices

- **models.py**: SQLModel class definitions with full relationships and type annotations
- **db.py**: Table creation utilities using SQLModel metadata
- **init_db.py**: Database initialization script using dependency injection container
- **loader.py**: Data ingestion with comprehensive validation, error handling, and bulk operations
- **queries.py**: Query/filter logic with type-safe SQLModel select operations
- **container.py**: Dependency injection for database engine and session management
- **config/**: Configuration management using Pydantic settings

**Best practices:**

- Use dependency injection container for database access throughout the application
- Leverage SQLModel relationships for efficient queries and data navigation
- Implement comprehensive validation in loader functions before database insertion
- Use Session context managers for all database operations
- Employ type hints consistently (modern Python syntax: `int | None` instead of `Optional[int]`)
- Separate concerns: configuration, dependency injection, data models, business logic

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
