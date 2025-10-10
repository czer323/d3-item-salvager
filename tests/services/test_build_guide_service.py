"""Unit tests for :mod:`d3_item_salvager.services.build_guide_service`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from d3_item_salvager.data.models import Build, Item, ItemUsage, Profile
from d3_item_salvager.exceptions.scraping import ScrapingError
from d3_item_salvager.maxroll_parser.maxroll_exceptions import GuideFetchError
from d3_item_salvager.maxroll_parser.types import (
    BuildProfileData,
    BuildProfileItems,
    GuideInfo,
    ItemMeta,
    ItemSlot,
    ItemUsageContext,
)
from d3_item_salvager.services.build_guide_service import (
    BuildGuideDependencies,
    BuildGuideService,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class FakeLogger:
    """Lightweight logger capturing emitted messages for assertions."""

    def __init__(self) -> None:
        self.infos: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.warnings: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.errors: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.exceptions: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def debug(self, message: str, *args: object, **kwargs: object) -> None:
        """Capture debug-level log call."""
        self.infos.append((message, args, dict(kwargs)))

    def info(self, message: str, *args: object, **kwargs: object) -> None:
        """Capture info-level log call."""
        self.infos.append((message, args, dict(kwargs)))

    def warning(self, message: str, *args: object, **kwargs: object) -> None:
        """Capture warning-level log call."""
        self.warnings.append((message, args, dict(kwargs)))

    def error(self, message: str, *args: object, **kwargs: object) -> None:
        """Capture error-level log call."""
        self.errors.append((message, args, dict(kwargs)))

    def exception(self, message: str, *args: object, **kwargs: object) -> None:
        """Capture exception-level log call."""
        self.exceptions.append((message, args, dict(kwargs)))


class FakeGuideFetcher:
    """Guide fetcher that returns a pre-defined collection of guides."""

    def __init__(self, guides: list[GuideInfo]) -> None:
        self._guides = list(guides)

    def fetch_guides(
        self,
        search: str | None = None,
        *,
        force_refresh: bool = False,
    ) -> list[GuideInfo]:
        """Return guides, optionally filtered by *search*."""
        _ = force_refresh
        if search is None:
            return list(self._guides)
        return [guide for guide in self._guides if search.lower() in guide.name.lower()]

    def get_guide_by_id(self, guide_id: str) -> GuideInfo | None:
        """Return a guide whose URL matches *guide_id* (acts as stand-in ID)."""
        return next((guide for guide in self._guides if guide.url == guide_id), None)


class FakeParser:
    """Parser that returns supplied profiles and item usages."""

    def __init__(
        self,
        profiles: list[BuildProfileData],
        usages: list[BuildProfileItems],
    ) -> None:
        self.profiles = list(profiles)
        self._usages = list(usages)

    def extract_usages(self) -> list[BuildProfileItems]:
        """Return the stored item usage payload."""
        return list(self._usages)

    def parse_profile(self, file_path: str) -> object:
        """Simulate parsing and record the requested *file_path*."""
        return {"parsed_from": file_path}


class FakeItemDataProvider:
    """Item data provider backed by an in-memory mapping."""

    def __init__(self, catalog: dict[str, ItemMeta]) -> None:
        self._catalog = dict(catalog)

    def get_item(self, item_id: str) -> ItemMeta | None:
        """Return metadata for *item_id* if available."""
        return self._catalog.get(item_id)

    def get_all_items(self) -> dict[str, ItemMeta]:
        """Return a copy of the catalog for isolation."""
        return dict(self._catalog)


@pytest.fixture
def engine_factory() -> Callable[[], Session]:
    """Provide a callable that yields a new SQLModel session against an in-memory DB."""
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)

    def make_session() -> Session:
        return Session(engine)

    return make_session


def _build_service(
    *,
    session_factory: Callable[[], Session],
    guides: list[GuideInfo],
    profiles: list[BuildProfileData],
    usages: list[BuildProfileItems],
    item_catalog: dict[str, ItemMeta],
) -> tuple[BuildGuideService, FakeLogger]:
    logger = FakeLogger()
    dependencies = BuildGuideDependencies(
        session_factory=session_factory,
        guide_fetcher=FakeGuideFetcher(guides),
        parser_factory=lambda _url: FakeParser(profiles, usages),
        item_data_provider=FakeItemDataProvider(item_catalog),
    )
    service = BuildGuideService(
        config=object(),  # type: ignore[arg-type]
        logger=logger,
        dependencies=dependencies,
    )
    return service, logger


def test_prepare_database_persists_expected_entities(
    engine_factory: Callable[[], Session],
) -> None:
    """Service orchestrates fetch, parse, and persistence into the SQLModel database."""
    guide = GuideInfo(name="test guide", url="/tmp/guide.json")
    profiles = [
        BuildProfileData(name="Profile A", class_name="Wizard"),
        BuildProfileData(name="Profile B", class_name="Barbarian"),
    ]
    usages = [
        BuildProfileItems(
            profile_name="Profile A",
            item_id="item-1",
            slot=ItemSlot.HEAD,
            usage_context=ItemUsageContext.MAIN,
        )
    ]
    catalog = {
        "item-1": ItemMeta(
            id="item-1",
            name="Mystic Helm",
            type="helm",
            quality="legendary",
        ),
    }

    service, _ = _build_service(
        session_factory=engine_factory,
        guides=[guide],
        profiles=profiles,
        usages=usages,
        item_catalog=catalog,
    )

    summary = service.prepare_database(force_refresh=True)

    assert summary.guides_processed == 1
    assert summary.guides_skipped == 0
    assert summary.builds_created == 1
    assert summary.profiles_created == 2
    assert summary.items_created == 1
    assert summary.usages_created == 1

    with engine_factory() as session:
        assert session.exec(select(Build)).all()
        assert len(session.exec(select(Profile)).all()) == 2
        assert len(session.exec(select(Item)).all()) == 1
        assert len(session.exec(select(ItemUsage)).all()) == 1


def test_prepare_database_is_idempotent(engine_factory: Callable[[], Session]) -> None:
    """A second run should not insert duplicate builds, profiles, or item usages."""
    guide = GuideInfo(name="repeat guide", url="/tmp/guide.json")
    profiles = [BuildProfileData(name="Solo", class_name="Necromancer")]
    usages = [
        BuildProfileItems(
            profile_name="Solo",
            item_id="item-42",
            slot=ItemSlot.WEAPON,
            usage_context=ItemUsageContext.MAIN,
        )
    ]
    catalog = {
        "item-42": ItemMeta(
            id="item-42",
            name="Spectral Scythe",
            type="scythe",
            quality="legendary",
        ),
    }

    service, _ = _build_service(
        session_factory=engine_factory,
        guides=[guide],
        profiles=profiles,
        usages=usages,
        item_catalog=catalog,
    )

    first = service.prepare_database(force_refresh=True)
    second = service.prepare_database(force_refresh=True)

    assert first.builds_created == 1
    assert second.builds_created == 0
    assert second.profiles_created == 0
    assert second.items_created == 0
    assert second.usages_created == 0

    with engine_factory() as session:
        assert len(session.exec(select(Build)).all()) == 1
        assert len(session.exec(select(Profile)).all()) == 1
        assert len(session.exec(select(Item)).all()) == 1
        assert len(session.exec(select(ItemUsage)).all()) == 1


def test_prepare_database_records_skipped_guides(
    engine_factory: Callable[[], Session],
) -> None:
    """Guides without profiles are reported as skipped and the database remains unchanged."""
    guide = GuideInfo(name="empty", url="/tmp/missing.json")

    def parser_factory(_url: str) -> FakeParser:
        return FakeParser([], [])

    logger = FakeLogger()
    dependencies = BuildGuideDependencies(
        session_factory=engine_factory,
        guide_fetcher=FakeGuideFetcher([guide]),
        parser_factory=parser_factory,
        item_data_provider=FakeItemDataProvider({}),
    )
    service = BuildGuideService(
        config=object(),  # type: ignore[arg-type]
        logger=logger,
        dependencies=dependencies,
    )

    summary = service.prepare_database(force_refresh=True)

    assert summary.guides_processed == 1
    assert summary.guides_skipped == 1
    assert summary.builds_created == 0


def test_fetch_guides_raises_scraping_error(
    engine_factory: Callable[[], Session],
) -> None:
    """Scraping failures surface as domain-specific `ScrapingError`."""

    class FailingFetcher(FakeGuideFetcher):
        """Guide fetcher that raises for test coverage."""

        def fetch_guides(
            self,
            search: str | None = None,
            *,
            force_refresh: bool = False,
        ) -> list[GuideInfo]:
            _ = force_refresh
            _ = search
            message = "boom"
            raise GuideFetchError(message)

    logger = FakeLogger()
    dependencies = BuildGuideDependencies(
        session_factory=engine_factory,
        guide_fetcher=FailingFetcher([]),
        parser_factory=lambda _url: FakeParser([], []),
        item_data_provider=FakeItemDataProvider({}),
    )
    service = BuildGuideService(
        config=object(),  # type: ignore[arg-type]
        logger=logger,
        dependencies=dependencies,
    )

    with pytest.raises(ScrapingError):
        service.fetch_guides(force_refresh=True)
    assert logger.exceptions
