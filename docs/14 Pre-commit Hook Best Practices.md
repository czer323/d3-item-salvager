# Pre-commit Hook Best Practices for d3-item-salvager

This guide explains how we use pre-commit hooks to keep our codebase clean and consistent before pushing changes. It is tailored for this project, which uses ruff, pylint, pyright, and mypy for linting and type checking.

## Why Use Pre-commit Hooks?

- Catch issues early, before code reaches CI/CD or other contributors.
- Enforce code style, linting, type safety, and prevent secrets or large files from being committed.
- Save CI resources by blocking bad commits locally.
- Works for Python and other languages (Node.js, Go, Ruby, Rust, shell, Docker, etc.)

## Setup Instructions

1. **Install pre-commit (one-time):**

   ```bash
   pip install pre-commit
   ```

2. **Add a `.pre-commit-config.yaml` file to the project root:**
   Example configuration for this project:

  ```yaml

  repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    # Ruff version.
    rev: v0.12.7
    hooks:
      # Run the linter.
      - id: ruff-check
        args: [ --fix ]
      # Run the formatter.
      - id: ruff-format

    - repo: <https://github.com/pre-commit/mirrors-mypy>
        rev: v1.8.0
        hooks:
      - id: mypy
    # - repo: <https://github.com/pre-commit/pre-commit-hooks>
    #      rev: v4.5.0
    #      hooks:
    #   - id: check-added-large-files
    #   - id: check-merge-conflict
    #   - id: detect-aws-credentials
    #   - id: trailing-whitespace
    #   - id: end-of-file-fixer
    #   - id: check-yaml
    - repo: local
        hooks:
      - id: pyright
        name: pyright
        entry: uv run pyright
        language: system
        types: [python]
      - id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        require_serial: true

    ```

3. **Install the hooks:**

  ```bash
  pre-commit install
  ```

4. **(Optional) Install hooks for other git events:**

   ```bash
   pre-commit install --hook-type pre-push --hook-type commit-msg
   ```

## Required Linting and Type Checking Tools

- **Ruff:** Fast Python linter and formatter. Configured via `ruff.toml` or `[tool.ruff]` in `pyproject.toml`.
- **Pylint:** Python static code analysis. Recent versions support `[tool.pylint]` in `pyproject.toml`, or use `.pylintrc`.
- **Pyright:** Type checker for Python. No config file needed unless you want custom settings (`pyrightconfig.json`).
- **Mypy:** Static type checker. Supports `[tool.mypy]` in `pyproject.toml`.

## Example Centralized Configuration

Most settings can be placed in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pylint]
disable = ["C0114", "C0115", "C0116"]
max-line-length = 120
```

Pyright uses sensible defaults. If you want custom settings, create `pyrightconfig.json`:

```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.12"
}
```

## How Hooks Work

- Hooks run automatically on `git commit`.
- If a hook fails, the commit is blocked. Fix the issues, stage changes, and recommit.
- To run all hooks manually:

  ```bash
  pre-commit run --all-files
  ```

- To run only specific hooks:

  ```bash
  pre-commit run ruff --all-files
  ```

- To skip specific hooks for a commit:

  ```bash
  SKIP=ruff git commit -m "skip ruff"
  ```

## Keeping Hooks Up to Date

- Run `pre-commit autoupdate` regularly to update hook versions in your config.
- Alternatively, use the [pre-commit-update](https://gitlab.com/vojko.pribudic.foss/pre-commit-update) tool to automate updates.
- You can run it manually:

  ```bash
  pre-commit-update
  ```

- Or schedule it in CI for regular updates.
- You can also add it as a local hook in your `.pre-commit-config.yaml`:

  ```yaml
  - repo: <https://gitlab.com/vojko.pribudic.foss/pre-commit-update>
    rev: v0.8.0  # Insert the latest tag here
    hooks:
    - id: pre-commit-update
        # Example args (use your own configuration)
        args: [--dry-run, --exclude, black, --keep, isort, --tag-prefix, black, custom-version-v]
  ```

- Note: Running this as a hook will update your `.pre-commit-config.yaml` automatically when you commit, which may cause frequent config changes. Use with care and consider restricting to manual or CI usage for most teams.

## CI/CD Integration

- Run `pre-commit run --all-files` in CI pipelines to check the entire codebase.
- Cache the pre-commit environments for faster CI builds.

## Best Practices

- Always run hooks before pushing code.
- Fix all issues reported by hooks before committing.
- Update `.pre-commit-config.yaml` as new tools or checks are needed.
- Never bypass hooks unless absolutely necessary (and document why).
- Use immutable versions for hooks (`rev:` should be a tag or SHA, not a branch name).
- Add a pre-commit badge to your README:

  ```markdown
  [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
  ```

## Troubleshooting

- If a hook fails, read the error message and fix the issue before retrying.
- If you need to skip hooks for a commit (not recommended), use:

  ```bash
  git commit --no-verify
  ```

  or

  ```bash
  SKIP=hookid git commit -m "skip hook"
  ```

  *Always document why you skipped hooks.*

## References

- [pre-commit Documentation](https://pre-commit.com/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [pylint Documentation](https://pylint.readthedocs.io/en/latest/)
- [pyright Documentation](https://github.com/microsoft/pyright)
- [mypy Documentation](https://mypy.readthedocs.io/en/stable/)
- [pre-commit Supported Languages](https://pre-commit.com/hooks.html#supported-hooks)
