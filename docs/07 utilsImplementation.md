# Utility/Helper Modules – Implementation Plan

## Domain & Purpose

Provides shared, domain-agnostic utilities (string manipulation, date handling, validation, etc.) for use across all modules. Ensures code reuse and keeps business logic clean.

## Directory Structure

```directory
src/d3_item_salvager/utils/
    __init__.py
    string_utils.py
    date_utils.py
    validation.py
```

## Tools & Libraries

- Python stdlib

## Design Patterns

- Pure functions, stateless
- Group by domain (string, date, validation)

## Key Functions & Classes

- `slugify()`, `normalize_name()`: String utilities
- `parse_date()`, `format_date()`: Date utilities
- `validate_item_id()`: Validation helpers

## Implementation Details

- Keep utility functions small and focused
- Document with Google-style docstrings
- Never mix business logic into utilities
- Example usage:

  ```python
  from d3_item_salvager.utils.string_utils import slugify
  slug = slugify("Ancient Legendary Sword")
  ```

- Utilities should be imported and reused across modules

## Testing & Extensibility

- Unit tests for all utility functions
- Add new utilities by creating new modules or extending existing ones
- Document all utility changes in this file and in code docstrings

## Example Utility Function

```python
def slugify(name: str) -> str:
    """Convert a string to a URL-friendly slug."""
    return name.lower().replace(" ", "-")
```

## Summary

This module provides reusable, stateless utility functions for the project. All utilities must be documented, tested, and kept separate from business logic for maintainability and clarity.
