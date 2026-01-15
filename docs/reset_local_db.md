# Reset Local DB Runbook

This runbook documents how to safely reset the local SQLite development database and how to use migrations.

## Quick commands

- Backup and reset using SQLModel (legacy):

  python -m d3_item_salvager.scripts.reset_local_db --db sqlite:///d3_items.db --confirm

- Use Alembic migrations to recreate schema (preferred):

  python -m d3_item_salvager.scripts.reset_local_db --db sqlite:///d3_items.db --use-migrations --confirm

Notes:

- The script creates a backup copy and a SQL dump before performing destructive operations.
- The `--use-migrations` flag runs `alembic upgrade head` to apply migrations; if Alembic is not available the script falls back to SQLModel metadata.
- Do NOT run these commands against a production database unless you pass `--force` and understand the consequences.

## Behavior (data and schema)

- Default reset behavior (recommended for local dev):
  1. **Backup:** The script saves a copy of the SQLite file and creates an SQL dump under `backups/`.
  2. **Drop:** If `--method drop` (default) the existing schema is dropped (this removes existing rows).
  3. **Recreate schema:** If `--use-migrations` is provided the script runs `alembic upgrade head` (replaying migrations to build the schema); otherwise it uses `SQLModel.metadata.create_all()` to create tables directly.
  4. **Repopulate:** Importer scripts run (e.g., `import_guides`, `load_reference_data`) to repopulate the database from canonical reference sources (Maxroll-derived imports and repository reference data).

- Important: Using `--use-migrations` with the default `--method drop` does **not** preserve or attempt to merge the data that was dropped. The reset workflow intentionally replaces the live content with the canonical importer output — it does not perform conflict resolution or incremental merging with previously stored rows.

- In-place migrations vs reset:
  - **In-place migration (preserve data):** If your goal is to upgrade an existing DB while preserving and transforming its data, run `alembic upgrade head` against the existing database (do **not** run `reset_local_db --method drop`). Ensure your Alembic migrations include any required data transformation steps (ALTER TABLE, data migration scripts).
  - **Reset + repopulate (replace data):** Use `reset_local_db --use-migrations --confirm` when you want a clean, reproducible dev DB built from migrations and canonical reference imports; this will replace previous data.

## Examples

- Reset and repopulate using migrations (preferred for dev):

  python -m d3_item_salvager.scripts.reset_local_db --db sqlite:///d3_items.db --use-migrations --confirm

- Run migrations in-place (preserve and transform existing data):

  alembic -c alembic.ini upgrade head

## Best practices

- Always verify the backup files in `backups/` after a reset and before running any restore. ✅
- Use `--dry-run` to preview non-destructively when experimenting. ✅
- For production systems, prefer running targeted `alembic upgrade` (in-place) with well-tested migrations that include data transformation steps; avoid the destructive `--method drop` on production unless you intentionally want to replace the data. ⚠️
