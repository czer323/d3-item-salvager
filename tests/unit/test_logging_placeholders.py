from pathlib import Path
from types import SimpleNamespace
from typing import Any

from loguru import logger

from d3_item_salvager.logging.adapters import get_loguru_service_logger
from d3_item_salvager.maxroll_parser.guide_cache import FileGuideCache
from d3_item_salvager.services.build_guide_service import (
    BuildGuideDependencies,
    BuildGuideService,
)


def test_file_guide_cache_logs_interpolated_values(tmp_path: Path) -> None:
    # Capture Loguru messages
    messages: list[str] = []
    sink_id = logger.add(lambda msg: messages.append(msg), format="{message}")

    try:
        # Create fake config with cache path
        cache_file = tmp_path / "guides.json"
        mp_cfg = SimpleNamespace(cache_file=cache_file, cache_ttl=60)
        cfg = SimpleNamespace(maxroll_parser=mp_cfg)

        cache = FileGuideCache(cfg)  # type: ignore[arg-type]

        # Create two simple guide-like objects
        guides = [
            SimpleNamespace(name="A", url="/a"),
            SimpleNamespace(name="B", url="/b"),
        ]

        cache.save(guides)  # type: ignore[arg-type]

        # Ensure we logged a saved message that contains the numeric count
        saved_msgs = [m for m in messages if "Saved" in m]
        assert any("Saved 2 guides to file cache" in m for m in saved_msgs)
        # Ensure no literal printf placeholder remains
        assert all("%d" not in m and "%s" not in m for m in saved_msgs)

        # Now call load to ensure loaded message is interpolated
        cache.load()
        loaded_msgs = [m for m in messages if "Loaded" in m]
        assert any("Loaded" in m and "guides" in m for m in loaded_msgs)
        assert all("%d" not in m and "%s" not in m for m in loaded_msgs)
    finally:
        logger.remove(sink_id)


def test_build_guide_fetch_logs_count() -> None:
    messages: list[str] = []
    sink_id = logger.add(lambda msg: messages.append(msg), format="{message}")

    try:
        # Dummy guide fetcher with correct signature
        class DummyFetcher:
            def fetch_guides(
                self, search: str | None = None, *, force_refresh: bool = False
            ) -> list[int]:
                # satisfy signature while keeping implementation simple
                _ = search
                _ = force_refresh
                return [1, 2, 3]

            def get_guide_by_id(self, guide_id: str) -> None:
                _ = guide_id
                return None

        from sqlmodel import Session

        def _session_factory() -> Session:  # type: ignore[return-value]
            msg = "Not used in test"
            raise RuntimeError(msg)

        deps: Any = BuildGuideDependencies(
            session_factory=_session_factory,
            guide_fetcher=DummyFetcher(),
        )  # type: ignore

        from d3_item_salvager.config.settings import AppConfig

        svc: Any = BuildGuideService(
            config=AppConfig(),
            logger=get_loguru_service_logger(),
            dependencies=deps,
        )  # type: ignore

        guides = svc.fetch_guides()

        # Assert fetched guides length is correct and log is interpolated
        assert len(guides) == 3
        info_msgs = [m for m in messages if "Fetched" in m]
        assert any("Fetched 3 guides from Maxroll" in m for m in info_msgs)
        assert all("%d" not in m and "%s" not in m for m in info_msgs)
    finally:
        logger.remove(sink_id)
