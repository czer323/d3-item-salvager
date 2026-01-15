"""Unit tests to ensure multi-planner guides are split into separate bundles."""

from typing import Any, Protocol, cast

from d3_item_salvager.maxroll_parser.types import BuildProfileData, BuildProfileItems
from d3_item_salvager.services.build_guide_service import (
    BuildGuideDependencies,
    BuildGuideService,
)


class _FakeGuideFetcher:
    def __init__(self, guides: list[Any]) -> None:
        self._guides = guides

    def fetch_guides(self, *_: object, **__: object) -> list[Any]:
        return self._guides

    def get_guide_by_id(self, guide_id: str) -> Any:  # noqa: ANN401
        _ = guide_id
        return None


class _Parser(Protocol):
    profiles: list[BuildProfileData]

    def extract_usages(self) -> list[BuildProfileItems]: ...

    def parse_profile(self, file_path: str) -> "_Parser": ...


class _FakeParser:
    def __init__(
        self, profiles: list[BuildProfileData], usages: list[BuildProfileItems]
    ) -> None:
        self.profiles = profiles
        self._usages = usages

    def extract_usages(self) -> list[BuildProfileItems]:
        return self._usages

    def parse_profile(self, file_path: str) -> "_FakeParser":
        _ = file_path
        return self


def test_build_profiles_from_multi_planner_guide(mocker: Any) -> None:  # noqa: ANN401
    # Setup a fake guide that would contain two planner ids
    guide_info_stub = mocker.stub(name="GuideInfo")
    guide = guide_info_stub(
        name="Sample Guide", url="https://maxroll.gg/d3/guides/sample"
    )

    # Fake resolver that reports two planner ids
    class FakeResolver:
        def get_planner_ids(self, url: str) -> list[str]:
            _ = url
            return ["123", "456"]

    # Fake parser factory that returns different profiles per planner URL
    def parser_factory(path: str) -> _Parser:
        if "123" in path:
            profiles = [BuildProfileData(name="A", class_name="Monk")]
            usages = [
                BuildProfileItems(
                    profile_name="A",
                    item_id="I1",
                    slot=cast("Any", None),
                    usage_context=cast("Any", None),
                )
            ]
            return cast("_Parser", _FakeParser(profiles, usages))
        if "456" in path:
            profiles = [BuildProfileData(name="B", class_name="Wizard")]
            usages = [
                BuildProfileItems(
                    profile_name="B",
                    item_id="I2",
                    slot=cast("Any", None),
                    usage_context=cast("Any", None),
                )
            ]
            return cast("_Parser", _FakeParser(profiles, usages))
        raise FileNotFoundError

    deps = BuildGuideDependencies(
        session_factory=cast("Any", lambda: None),
        guide_fetcher=cast("Any", _FakeGuideFetcher([guide])),
        parser_factory=cast("Any", parser_factory),
        guide_profile_resolver=cast("Any", FakeResolver()),
    )

    # Minimal config stub with planner_profile_url used when building planner-specific URLs
    class Cfg:
        maxroll_parser: Any

    cfg = Cfg()
    cfg.maxroll_parser = type(
        "x",
        (),
        {
            "planner_profile_url": "https://planners.maxroll.gg/profiles/load/d3/{planner_id}"
        },
    )()

    svc = BuildGuideService(
        config=cast("Any", cfg), logger=mocker.stub(), dependencies=deps
    )

    bundles, skipped = svc.build_profiles_from_guides(cast("Any", [guide]))
    assert skipped == 0
    assert len(bundles) == 2
    names = [[p.name for p in b.profiles] for b in bundles]
    assert ["A"] in names
    assert ["B"] in names
