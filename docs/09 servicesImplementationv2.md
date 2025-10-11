---
goal: "Implement services module for business logic and orchestration"
version: 1.0
date_created: 2025-08-13
last_updated: 2025-10-09
owner: "d3-item-salvager team"
status: 'In Progress'
tags: [feature, architecture, services, orchestration, business-logic]
---

# Introduction

![Status: In Progress](https://img.shields.io/badge/status-In%20Progress-orange)

This plan establishes a generic, extensible services framework for business logic and orchestration in the Diablo 3 build guide item scraper project. The services module will encapsulate business logic and orchestration, exposing APIs for workers (using Dramatiq) to trigger scraping, parsing, and database update operations. The module will not execute scheduled jobs directly; it will provide stateless, idempotent methods for use by the workers module and other components. The initial concrete implementation is `BuildGuideService`, but the framework is designed to support additional services (e.g., item, profile, or other domain-specific logic) as project needs evolve.

## Project Architectural Conventions

To ensure consistency and maintainability, all services must follow these architectural conventions established in the codebase:

- **Dependency Injection via Container**: All service classes must be instantiated and resolved through the project’s DI container (`src/d3_item_salvager/container.py`). Configuration, logging, and other dependencies are injected via constructor or factory methods.

- **Configuration Management**: Services must use centralized configuration objects from `src/d3_item_salvager/config/`, with environment/config values injected via the container.

- **Logging**: All services must use the project’s logging module, specifically Loguru (`src/d3_item_salvager/logging/`), and avoid direct use of `print` or ad-hoc loggers.

- **Error Handling**: Use custom exceptions from `src/d3_item_salvager/exceptions/` and propagate errors in a standardized way.

- **Data Access Layer**: Services should interact with the database only via repository/data access abstractions in `src/d3_item_salvager/data/`, not direct SQL or ORM calls.

- **Testing Conventions**: All public service methods must be covered by unit and integration tests, using mocks/fakes for dependencies. Tests are located in `tests/services/` and follow project test structure.

- **Statelessness and Idempotency**: Services must be stateless and idempotent. Patterns enforcing this should be documented and followed.

- **Extensibility**: New services should inherit from any base classes or interfaces provided, and follow naming, structure, and documentation conventions.

- **Security and Secrets**: Secrets must be managed via configuration and injected securely; never hardcoded in service code.

- **API Exposure**: Service APIs are exposed to workers, API, CLI, etc. via public methods and documented interface contracts.

Refer to the relevant modules for implementation details and examples.

## 1. Requirements & Constraints

- **REQ-001**: Service methods must encapsulate business logic for scraping, parsing, and database operations.
- **REQ-002**: Service APIs must be callable by workers and other modules (API, CLI, etc.).
- **REQ-003**: Service methods must be stateless, idempotent, and not manage scheduling or concurrency.
- **SEC-001**: Handle secrets/config securely; avoid leaking sensitive data in logs.
- **CON-001**: No scheduling, concurrency, or job management code in services (handled by workers/Dramatiq).
- **GUD-001**: Use dependency injection for configuration and logging.
- **PAT-001**: Follow project conventions for module structure and naming.
- **PAT-002**: Expose clear, documented interfaces for worker integration.

- **PAT-003**: All future services must follow the same stateless, dependency-injected, documented structure, and be placed in the `src/d3_item_salvager/services/` directory.

## 2. Implementation Steps

### Implementation Phase 1

- GOAL-001: Design and implement service interfaces and class structure

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-001 | Create `src/d3_item_salvager/services/build_guide_service.py` with class `BuildGuideService` | ✅ | 2025-10-09 |
| TASK-002 | Define public methods for scraping, parsing, and database operations | ✅ | 2025-10-09 |
| TASK-003 | Implement dependency injection for config and logging | ✅ | 2025-10-09 |

### Implementation Phase 2

- GOAL-002: Integrate business logic and document service APIs

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-004 | Implement scraping logic in `BuildGuideService` | ✅ | 2025-10-09 |
| TASK-005 | Implement parsing and transformation logic in `BuildGuideService` | ✅ | 2025-10-09 |
| TASK-006 | Implement database update/insert logic in `BuildGuideService` | ✅ | 2025-10-09 |
| TASK-007 | Document service APIs for worker integration | ✅ | 2025-10-09 |

### Implementation Phase 3

- GOAL-003: Add error handling, logging, and testing

| Task | Description | Completed | Date |
|------|-------------|-----------|------|
| TASK-008 | Add error handling and logging to all service methods | ✅ | 2025-10-09 |
| TASK-009 | Write unit and integration tests in `tests/services/test_build_guide_service.py` | ✅ | 2025-10-09 |
| TASK-010 | Provide usage examples for worker integration | ☐ | TBD |

## 3. Alternatives

- **ALT-001**: Combine business logic and worker scheduling in a single module (rejected for separation of concerns and maintainability).
- **ALT-002**: Use a microservice architecture for services (rejected for project scope and complexity).

## 4. Dependencies

- **DEP-001**: Dramatiq (for job scheduling in workers module)
- **DEP-002**: Database driver (e.g., SQLite, PostgreSQL, as used in project)
- **DEP-003**: Configuration and logging modules (as defined in project)
- **DEP-004**: Scraping/parsing libraries (e.g., requests, beautifulsoup4, cloudscraper)

## 5. Files

- **FILE-001**: `src/d3_item_salvager/services/build_guide_service.py` (new)
- **FILE-002**: `tests/services/test_build_guide_service.py` (new)
- **FILE-003**: `src/d3_item_salvager/config/` (reference for dependency injection)
- **FILE-004**: `src/d3_item_salvager/logging/` (reference for dependency injection)

## 6. Testing

- **TEST-001**: Unit tests for orchestration branches using fakes (`tests/services/test_build_guide_service.py`)
- **TEST-002**: Integration tests against an in-memory SQLModel database validating persistence behaviour
- **TEST-003**: Error handling tests covering scraper/parser failures and idempotency checks

## 7. Risks & Assumptions

- **RISK-001**: API/HTML structure changes on Maxroll may break scraping logic.
- **RISK-002**: Data consistency and idempotency issues if service methods are not carefully designed.
- **RISK-003**: Unexpected data formats or missing fields.
- **ASSUMPTION-001**: Workers module will handle scheduling, retries, and concurrency using Dramatiq.
- **ASSUMPTION-002**: Configuration and logging modules are available for dependency injection.

## 8. Related Specifications / Further Reading

- [docs/00 implementationPlan.md](../docs/00%20implementationPlan.md)
- [Dramatiq documentation](https://dramatiq.io/)
- [BeautifulSoup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Project configuration and logging modules]
