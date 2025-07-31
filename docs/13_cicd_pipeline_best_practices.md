
# CI/CD Pipeline Best Practices for d3-item-salvager

This document outlines recommended best practices for designing, implementing, and maintaining a robust CI/CD pipeline for the d3-item-salvager project using GitHub Actions, with a focus on `uv` package management, pre-commit hooks, and advanced GitHub Actions concepts for security, reliability, and performance.

## 1. Introduction

Continuous Integration and Continuous Deployment (CI/CD) automates code quality checks, testing, and deployment. GitHub Actions is a flexible, cloud-native solution that integrates directly with your repository.

## 2. Workflow Structure & Modularity

- **Naming:** Use descriptive workflow file names (e.g., `ci.yml`, `deploy.yml`).
- **Triggers:** Use `on: push`, `on: pull_request`, and `on: workflow_dispatch` for manual runs.
- **Concurrency:** Prevent race conditions with `concurrency` groups.
- **Permissions:** Set least-privilege permissions for `GITHUB_TOKEN` at both workflow and job level. Document which jobs need write access and why.
- **Reusable Workflows:** Use `workflow_call` to modularize common patterns (e.g., test, build, deploy) and reduce duplication.
- **Package Management:** Use `uv` for all dependency installation and environment management. Always commit `uv.lock` for reproducible builds.

**Example:**

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
permissions:
  contents: read
jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: uv sync --dev
```

## 3. Jobs, Steps, and Matrix Strategies

- **Separation:** Use jobs for lint, test, build, deploy, security scan, etc.
- **Dependencies:** Use `needs:` to control job order.
- **Outputs:** Pass data between jobs with `outputs:`.
- **Conditional Execution:** Use `if:` for branch/environment logic (e.g., deploy only on `main`).
- **Tool Execution:** Use `uv run` for all tools (lint, type check, test) to ensure correct environment.
- **Matrix Strategies:** Use `strategy.matrix` to test across Python versions and OSes for compatibility and faster feedback.

**Example:**

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: uv sync --dev
      - name: Lint
        run: uv run ruff check .
  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        python-version: [3.11, 3.12]
        os: [ubuntu-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: uv sync --dev
      - name: Run tests
        run: uv run pytest
```

## 4. Security Best Practices

- **Secrets:** Store secrets in GitHub repository/environments, never in code. Use environment-specific secrets and approval rules for production.
- **Token Permissions:** Restrict `GITHUB_TOKEN` to only needed scopes at workflow/job level. Document any write access.
- **Dependency Scanning:** Use `dependency-review-action` and SAST tools (e.g., CodeQL) to catch vulnerabilities early.
- **Secret Scanning:** Enable GitHub's built-in secret scanning and use pre-commit hooks for local secret checks.
- **OIDC Authentication:** Use OIDC for cloud authentication instead of static secrets for deployments.

**Example:**

```yaml
permissions:
  contents: read
  pull-requests: write
  checks: write
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Dependency Review
        uses: actions/dependency-review-action@v4
      - name: CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

## 5. Testing Strategy

- **Unit Tests:** Run on every push/PR. Use `pytest` and `scripts/check unit`.
- **Integration/E2E:** Use dedicated jobs and environments.
- **Reporting:** Upload test and coverage reports as artifacts.

**Example:**

```yaml
jobs:
  test:
    steps:
      - name: Run tests
        run: scripts/check unit
      - name: Upload coverage
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: coverage.xml
```

## 6. Deployment Strategy & Reliability

- **Staging/Production:** Use GitHub Environments for protection, manual approvals, and required reviewers.
- **Manual Approvals:** Require reviewers for production deploys and document approval steps.
- **Rollback:** Automate rollback on failure (e.g., previous artifact/image). Document and test rollback procedures.
- **Post-Deployment Health Checks:** Implement automated smoke tests and health checks after deployment. Trigger rollbacks if these fail.
- **Observability:** Upload deployment logs and test reports as artifacts. Configure alerts for deployment failures.

**Example:**

```yaml
jobs:
  deploy:
    environment:
      name: production
      url: https://yourapp.example.com
    steps:
      - name: Deploy
        run: ./deploy.sh
      - name: Post-deploy health check
        run: ./smoke_test.sh
      - name: Upload logs
        uses: actions/upload-artifact@v3
        with:
          name: deploy-logs
          path: logs/
```

## 7. Performance Optimization & Advanced Caching

- **Caching:** Use `actions/cache@v3` for dependencies and build outputs. For `uv`, cache `~/.cache/uv` and use both `uv.lock` and `pyproject.toml` for cache keys. Use `restore-keys` for fallback.
- **Matrix Strategies:** Test across Python versions and OSes using `strategy.matrix`.
- **Fast Checkout:** Use `actions/checkout@v4` with `fetch-depth: 1` for most jobs to speed up workflow execution.
- **Self-Hosted Runners:** Consider self-hosted runners for private resources or specialized hardware. Document setup and security.

**Example:**

```yaml
steps:
  - uses: actions/cache@v3
    with:
      path: ~/.cache/uv
      key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}-${{ hashFiles('**/pyproject.toml') }}
      restore-keys: ${{ runner.os }}-uv-
```

## 8. Monitoring, Observability & Artifacts

- **Logging:** Use STDOUT/STDERR for logs; upload logs and test reports as artifacts for debugging and compliance.
- **Alerts:** Configure notifications for failed workflows and deployment issues.
- **Artifacts:** Use `actions/upload-artifact` for test reports, coverage, and deployment logs. Set appropriate `retention-days`.

## 9. Troubleshooting & Maintenance

- **Common Issues:** Check triggers, permissions, cache keys, secrets, matrix config, and `uv.lock` changes.
- **Troubleshooting Tips:**
  - Validate cache keys and paths for cache hits/misses.
  - Review workflow logs for skipped jobs, permission errors, or timeouts.
  - Isolate flaky tests and run repeatedly to diagnose.
  - Use post-deployment health checks and logs for deployment failures.
  - Standardize environments between local and CI (Python version, dependencies).
- **Review Checklist:**
  - Clear workflow names and triggers
  - Explicit least-privilege permissions at workflow/job level
  - Caching and matrix strategies (with `uv`)
  - Comprehensive testing, reporting, and artifact uploads
  - Secure secret management and scanning
  - All dependencies managed via `uv` and `pyproject.toml`
  - Modular, reusable workflow design
  - Documented rollback and health check procedures

## 10. Pre-commit Hooks and Local Quality Checks

- **Purpose:** Pre-commit hooks run locally before code is committed, catching issues early and saving CI resources.
- **Setup:** Use the [pre-commit](https://pre-commit.com/) framework and configure hooks to use `uv run` for all checks.
- **Typical hooks:** Linting (`ruff`), formatting (`black`), type checking (`pyright`), secret scanning, and fast unit tests.
- **Config Example:**

```yaml
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-black
    rev: 23.3.0
    hooks:
      - id: black
```

- **Usage:**
  - Install hooks: `pre-commit install`
  - Run manually: `pre-commit run --all-files`
  - Configure hooks to use `uv run` for all Python tools.

## 11. How uv and Pre-commit Hooks Complement CI/CD

- **Pre-commit hooks** catch issues before code is committed, providing fast local feedback and keeping your repo clean.
- **CI/CD workflows** provide reproducible, team-wide validation, full test suites, and deployment automation.
- **Best practice:** Use both for maximum code quality, reliability, and developer efficiency.

## 12. References and Further Reading

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Python CI/CD Example](https://github.com/actions/starter-workflows/tree/main/ci/python)
- [uv Documentation](https://github.com/astral-sh/uv)
- [pre-commit Documentation](https://pre-commit.com/)

---

This guide should be reviewed and updated as your project evolves. For questions or improvements, open an issue or PR in the repository.
