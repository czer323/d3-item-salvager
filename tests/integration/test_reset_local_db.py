"""Integration tests for scripts.reset_local_db.reset_local_db"""

from pathlib import Path
from typing import cast

from _pytest.monkeypatch import MonkeyPatch
from sqlmodel import Session, create_engine, select

from d3_item_salvager.data.models import Build, ItemUsage, Profile
from d3_item_salvager.scripts import reset_local_db


def test_reset_local_db_creates_backups_and_imports(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    # Create an empty DB with tables
    engine = create_engine(db_url)
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)

    backups_dir = tmp_path / "backups"

    # Patch the heavy importer with a fast fake that inserts minimal data to validate repopulation
    def _fake_run_importers(url: str) -> None:
        from sqlmodel import Session

        from d3_item_salvager.data.models import Build, Item, ItemUsage, Profile

        eng = create_engine(url)
        with Session(eng) as s:
            b = Build(title="Fast Build", url="/fast-build")
            s.add(b)
            s.commit()
            s.refresh(b)
            p = Profile(build_id=cast("int", b.id), name="Fast", class_name="Monk")
            s.add(p)
            i = Item(id="I_FAST", name="Fast Sword", type="sword", quality="legendary")
            s.add(i)
            s.commit()
            s.refresh(p)
            usage = ItemUsage(
                profile_id=cast("int", p.id),
                item_id=i.id,
                slot="mainhand",
                usage_context="main",
            )
            s.add(usage)
            s.commit()

    monkeypatch.setattr(
        "d3_item_salvager.scripts.reset_local_db.run_importers",
        _fake_run_importers,
    )

    # Run the reset: confirm=True to allow destructive operations
    res = reset_local_db.reset_local_db(
        db_url=db_url, backup_dir=str(backups_dir), method="drop", confirm=True
    )

    assert res.backed_up_file is not None
    assert res.backed_up_file.exists()
    assert res.dumped_sql is not None
    assert res.dumped_sql.exists()

    # Verify DB has builds/profiles/item_usages inserted by the fake importer
    with Session(engine) as s:
        builds = s.exec(select(Build)).all()
        assert len(builds) == 1
        assert builds[0].title == "Fast Build"

        # Referential checks: every ItemUsage.profile_id must match a Profile.id
        usages = s.exec(select(ItemUsage)).all()
        profile_ids = {p.id for p in s.exec(select(Profile)).all() if p.id is not None}
        assert all(u.profile_id in profile_ids for u in usages), (
            "Found ItemUsage referencing missing Profile"
        )


def test_reset_local_db_dry_run(tmp_path: Path) -> None:
    db_path = tmp_path / "test2.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)

    backups_dir = tmp_path / "backups2"

    # Dry run should not create backups nor modify DB
    res = reset_local_db.reset_local_db(
        db_url=db_url, backup_dir=str(backups_dir), method="drop", dry_run=True
    )

    assert res.backed_up_file is None
    assert res.dumped_sql is None
    assert not backups_dir.exists()
