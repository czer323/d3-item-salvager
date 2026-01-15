"""Safe reset and repopulation script for local development DB.

Usage (programmatically or via CLI):

    python -m d3_item_salvager.scripts.reset_local_db --db sqlite:///d3_items.db --backup-dir backups --method drop --confirm

This module is importable and provides `reset_local_db` function for programmatic use
and `main()` for CLI use.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlmodel import SQLModel, create_engine

from d3_item_salvager.config.base import DatabaseConfig
from d3_item_salvager.scripts import import_guides
from d3_item_salvager.utility import load_reference_data


@dataclass
class Result:
    backed_up_file: Path | None = None
    dumped_sql: Path | None = None
    engine_url: str = ""


def _is_sqlite_file_url(url: str) -> bool:
    return url.startswith("sqlite:///") and not url.startswith("sqlite:///:memory:")


def _sqlite_path_from_url(url: str) -> Path:
    assert _is_sqlite_file_url(url)
    return Path(url.replace("sqlite:///", ""))


def backup_sqlite_file(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    bak = backup_dir / (db_path.name + ".bak")
    shutil.copy(db_path, bak)
    return bak


def dump_sqlite(db_path: Path, dump_path: Path) -> None:
    # Use Python's sqlite3 to create a dump to avoid relying on external sqlite3 binary
    conn = sqlite3.connect(str(db_path))
    with dump_path.open("w", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write(line)
            f.write("\n")
    conn.close()


def recreate_schema(db_url: str) -> None:
    engine = create_engine(db_url)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def run_importers(db_url: str) -> None:
    # Ensure importers use same DB by setting DATABASE_URL for the lifetime
    os.environ["DATABASE_URL"] = db_url
    # import_guides uses load_runtime_env() internally and Container() so simply call main
    import_guides.main()
    # load_reference_data.main is idempotent and loads sample reference builds
    load_reference_data.main()


def reset_local_db(
    db_url: str | None = None,
    backup_dir: str | Path | None = None,
    method: str = "drop",
    dry_run: bool = False,
    confirm: bool = False,
    force: bool = False,
) -> Result:
    db_url = db_url or DatabaseConfig().url
    res = Result(engine_url=db_url)

    if not _is_sqlite_file_url(db_url) and not force:
        msg = "Refusing to operate on non-sqlite DB without --force"
        raise SystemExit(msg)

    sqlite_path = _sqlite_path_from_url(db_url)

    if not sqlite_path.exists():
        msg = f"Database file not found: {sqlite_path}"
        raise FileNotFoundError(msg)

    final_backup_dir = Path(backup_dir or (Path.cwd() / "backups"))

    if dry_run:
        print(
            f"DRY RUN: Would backup {sqlite_path} to {final_backup_dir} and {method} recreate schema"
        )
        return res

    if not confirm:
        msg = "Destructive operation requires --confirm flag. Aborting."
        raise SystemExit(msg)

    # Backup file copy
    bak = backup_sqlite_file(sqlite_path, final_backup_dir)
    res.backed_up_file = bak

    # Dump SQL
    dump_path = final_backup_dir / (sqlite_path.name + ".sql")
    dump_sqlite(sqlite_path, dump_path)
    res.dumped_sql = dump_path

    # Perform cleanup
    if method == "drop":
        recreate_schema(db_url)
    elif method == "delete":
        # Not implemented: granular deletes are complex and depend on FK ordering.
        msg = "delete method not implemented; use 'drop' or implement later"
        raise NotImplementedError(msg)
    else:
        msg = "Unknown method"
        raise ValueError(msg)

    # Repopulate
    run_importers(db_url)

    return res


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser("reset_local_db")
    p.add_argument("--db", default=None, help="Database URL (sqlite:///path)")
    p.add_argument("--backup-dir", default=None, help="Directory to store backups")
    p.add_argument("--method", choices=("drop", "delete"), default="drop")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--confirm", action="store_true", help="Confirm destructive operation"
    )
    p.add_argument(
        "--force", action="store_true", help="Allow non-sqlite DBs (use with caution)"
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    args = _parse_args(argv)
    try:
        res = reset_local_db(
            db_url=args.db,
            backup_dir=args.backup_dir,
            method=args.method,
            dry_run=args.dry_run,
            confirm=args.confirm,
            force=args.force,
        )
    except Exception as exc:  # pragma: no cover - surface errors for CLI
        print("Error:", exc)
        return 1

    print("Backup saved:", res.backed_up_file)
    print("SQL dump:", res.dumped_sql)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
