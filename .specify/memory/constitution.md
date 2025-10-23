<!--
Sync Impact Report

Version change: (template) -> 1.0.0

Modified principles:
- I. Library‑First Design (added)
- II. CLI‑First Interface (added)
- III. Test‑First (NON‑NEGOTIABLE) (added)
- IV. Integration & Contract Testing (added)
- V. Observability, Versioning & Simplicity (added)

Added sections:
- Constraints & Security Requirements
- Development Workflow & Quality Gates
- Governance

Removed sections:
- None

Templates requiring updates:
- .specify/templates/plan-template.md ✅ updated
- .specify/templates/spec-template.md ⚠ pending
- .specify/templates/tasks-template.md ⚠ pending
- .specify/templates/checklist-template.md ⚠ pending
- .specify/templates/agent-file-template.md ⚠ pending

Follow-up TODOs:
- TODO(RATIFICATION_DATE): determine original adoption date and update constitution
- Manual review: ensure no remaining bracket tokens across repository templates
-->

# D3 Item Salvager Constitution

## Core Principles

### I. Library‑First Design

Every new feature or capability MUST begin as a well‑scoped, self‑contained library or module. Libraries
MUST have a single, clear purpose, public API surface, and automated unit tests. Reuse and composition are
preferred over duplication. Projects or teams MAY group libraries into higher level packages, but no logic
should be introduced that cannot be exercised and tested in isolation.

### II. CLI‑First Interface (when applicable)

Public user-facing functionality MUST expose a command‑line interface (or a clearly defined programmatic API)
that supports both machine and human consumption. When CLI is provided, the plan MUST document the text
I/O contract (stdin/args → stdout; errors → stderr) and MUST support a JSON output mode alongside a
human‑readable mode for scripting and automation.

### III. Test‑First (NON‑NEGOTIABLE)

All production code MUST be accompanied by tests. For new features, tests (unit or contract tests) SHOULD be
written before implementation where practical. Every change MUST include at least one automated test that
verifies the intended behavior. CI gates MUST run tests and block merges on failures.

### IV. Integration & Contract Testing

Changes that cross module/service boundaries, alter public contracts, or affect persisted data MUST include
integration and/or contract tests. Contract changes require a migration plan and explicit documentation of
compatibility expectations. Integration tests SHOULD target the smallest realistic scope that validates the
interaction (e.g., library contract + consumer smoke test).

### V. Observability, Versioning & Simplicity

All services and libraries MUST use structured logging and surface meaningful telemetry where appropriate
to aid debugging. Versioning MUST follow semantic versioning (MAJOR.MINOR.PATCH); breaking changes MUST
increment MAJOR and include a migration plan. Developers MUST prefer simplicity and YAGNI—avoid premature
abstraction; add complexity only when justified and documented.

## Constraints & Security Requirements

Technology and operational constraints for the project:

- Language: Python 3.12+ (use features safely and maintain compatibility with CI tooling)
- Type safety: All public APIs MUST include type annotations; pyright is used for static checking
- Configuration: Use frozen dataclasses for immutable configuration objects where practical
- Pre‑commit: `pre-commit` hooks (ruff, pyright) MUST pass before merging
- Secrets: Secrets (API keys, private keys) MUST NOT be committed to the repository. Secrets MUST be provided
  at runtime via environment variables or secure secret stores
- Dependencies: Add third‑party dependencies only after approval; prefer small, well‑maintained libraries

## Development Workflow & Quality Gates

- Branching: Feature branches SHOULD follow `type/short-description` (e.g., `feat/parser-add-source`)
- Commits: Use conventional commit messages (type(scope): subject)
- PRs: All PRs MUST include a description of the change, link to relevant spec/plan, and mention tests added
- Quality gates: `uv run pre-commit run --all-files`, `uv run pyright`, and `uv run pytest` MUST pass before
  merging. CI MUST run the same checks.
- Reviews: At least one approving review is required for non-trivial changes; maintainers may require more
  depending on risk.

## Governance

The constitution is the source of truth for project practices. Amendments to this document MUST follow the
process below:

1. Propose: Open an issue and attach a draft amendment (diff or PR) with rationale and migration steps.
2. Review: At least two maintainers MUST review and approve the proposed amendment.
3. Ratify: After approvals, merge the amendment PR and update the constitution `Version` and
   `Last Amended` date.
4. Communicate & Migrate: Notify contributors and update any templates or enforcement code (CI, scripts).

Minor clarifications (typo fixes, wording) MAY be direct‑merged by a maintainer but SHOULD still update the
`Last Amended` date and increment the PATCH version.

**Version**: 0.1.0 | **Ratified**: TODO(RATIFICATION_DATE): original adoption date unknown | **Last Amended**: 2025-10-23
