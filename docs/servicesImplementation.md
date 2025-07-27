# Service Layer / Business Logic Module – Implementation Plan

## Domain & Purpose

Encapsulates all business logic, orchestration, and workflows (e.g., recommendations, item analysis, user actions). Decouples raw data access from domain logic and ensures maintainability and testability.

## Directory Structure

```directory
src/d3_item_salvager/services/
    __init__.py
    item_recommendation.py   # Recommendation logic
    user_preferences.py      # User keep/ignore logic
    build_analysis.py        # Build/variant analysis
    orchestration.py         # Workflow orchestration
```

## Tools & Libraries

- Python stdlib
- Dependency injection (pass config, data access objects)

## Design Patterns

- Service classes (stateless, injected dependencies)
- Strategy pattern for recommendations
- Factory pattern for service instantiation
- Protocols for service interfaces

## Key Classes & Functions

- `ItemRecommendationService`: Main recommendation logic
- `UserPreferenceService`: Handles user keep/ignore lists
- `BuildAnalysisService`: Analyzes builds/variants
- `Orchestrator`: Coordinates workflows

## Implementation Details

- Never mix data access with business logic; always inject DAOs
- Document all public service methods
- Write unit tests for all business logic
- Use protocols for service interfaces to enable easy testing/mocking
- Example usage:

  ```python
  from d3_item_salvager.services.item_recommendation import ItemRecommendationService
  service = ItemRecommendationService(dao, config)
  recommendations = service.get_recommendations(user_id)
  ```

- Orchestrator should coordinate multi-step workflows and error handling

## Testing & Extensibility

- Unit tests for all service methods
- Add new services by creating new modules and updating orchestration
- Document all business logic changes in this file and in code docstrings

## Example Service Class

```python
class ItemRecommendationService:
    """Service for recommending items to keep or salvage."""
    def __init__(self, dao, config):
        self.dao = dao
        self.config = config
    def get_recommendations(self, user_id: str) -> list[str]:
        # Business logic here
        pass
```

## Summary

This module provides a clean, testable, and extensible service layer for all business logic. All workflows and recommendations are encapsulated in service classes, ensuring separation of concerns and maintainability.
