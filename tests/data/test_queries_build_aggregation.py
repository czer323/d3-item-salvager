from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from d3_item_salvager.data import queries
from d3_item_salvager.data.models import Build


def _make_engine() -> Engine:
    return create_engine("sqlite:///:memory:")


def test_aggregate_planner_builds_no_original() -> None:
    engine = _make_engine()
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        b1 = Build(
            title="Sample Guide (planner 123)",
            url="https://planners.maxroll.gg/profiles/load/d3/123",
        )
        b2 = Build(
            title="Sample Guide (planner 456)",
            url="https://planners.maxroll.gg/profiles/load/d3/456",
        )
        session.add(b1)
        session.add(b2)
        session.commit()

        builds, total = queries.list_builds(session)

        assert total == 1
        assert len(builds) == 1
        assert builds[0].title == "Sample Guide"
        # Representative URL falls back to first-seen planner URL when no non-planner URL exists
        assert builds[0].url in (b1.url, b2.url)


def test_prefer_non_planner_url_if_present() -> None:
    engine = _make_engine()
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        planner1 = Build(
            title="Sample Guide (planner 123)",
            url="https://planners.maxroll.gg/profiles/load/d3/123",
        )
        planner2 = Build(
            title="Sample Guide (planner 456)",
            url="https://planners.maxroll.gg/profiles/load/d3/456",
        )
        original = Build(
            title="Sample Guide", url="https://maxroll.gg/d3/guides/sample"
        )
        session.add_all([planner1, planner2, original])
        session.commit()

        builds, total = queries.list_builds(session)

        assert total == 1
        assert len(builds) == 1
        assert builds[0].title == "Sample Guide"
        # Representative URL should prefer the non-planner original guide URL
        assert builds[0].url == original.url
