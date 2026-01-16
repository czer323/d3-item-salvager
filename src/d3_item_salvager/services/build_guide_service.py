"""Service for orchestrating build guide scraping, parsing, and persistence."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from sqlmodel import Session, select

from d3_item_salvager.data.loader import (
    insert_build,
    insert_item_usages_with_validation,
    insert_items_from_dict,
    insert_profiles,
)
from d3_item_salvager.data.models import Build, Item, ItemUsage, Profile
from d3_item_salvager.exceptions.scraping import ScrapingError
from d3_item_salvager.maxroll_parser.build_profile_parser import BuildProfileParser
from d3_item_salvager.maxroll_parser.get_guide_urls import MaxrollGuideFetcher
from d3_item_salvager.maxroll_parser.guide_profile_resolver import GuideProfileResolver
from d3_item_salvager.maxroll_parser.item_data_parser import DataParser
from d3_item_salvager.maxroll_parser.maxroll_exceptions import (
    BuildProfileError,
    GuideFetchError,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from sqlalchemy.orm import InstrumentedAttribute

    from d3_item_salvager.config.settings import AppConfig
    from d3_item_salvager.maxroll_parser.types import (
        GuideInfo,
        ItemMeta,
    )
    from d3_item_salvager.services.protocols import (
        BuildItemUsagePayload,
        BuildProfilePayload,
        GuideFetcher,
        GuideList,
        ItemDataProvider,
        ParserFactory,
        ServiceLogger,
        SessionFactory,
    )


@dataclass(frozen=True, slots=True)
class ParsedGuideBundle:
    """Container for parsed guide data ready for persistence."""

    guide: GuideInfo
    profiles: BuildProfilePayload
    usages: BuildItemUsagePayload


@dataclass(frozen=True, slots=True)
class BuildSyncSummary:
    """Summary of database synchronization work performed by the service."""

    guides_processed: int
    guides_skipped: int
    builds_created: int
    profiles_created: int
    items_created: int
    usages_created: int


@dataclass(frozen=True, slots=True)
class BundleSyncResult:
    """Result of synchronizing a single parsed guide bundle."""

    builds_created: int
    profiles_created: int
    items_created: int
    usages_created: int


@dataclass(frozen=True, slots=True)
class BuildGuideDependencies:
    """Injected dependencies for :class:`BuildGuideService`."""

    session_factory: SessionFactory
    guide_fetcher: GuideFetcher | None = None
    parser_factory: ParserFactory | None = None
    item_data_provider: ItemDataProvider | None = None
    guide_profile_resolver: GuideProfileResolver | None = None


class BuildGuideService:
    """Encapsulates build guide scraping, parsing, and persistence workflows."""

    def __init__(
        self,
        config: AppConfig,
        logger: ServiceLogger,
        *,
        dependencies: BuildGuideDependencies,
    ) -> None:
        """Configure the service with its injected dependencies."""
        self._logger = logger
        self._config = config
        self._session_factory = dependencies.session_factory
        self._guide_fetcher: GuideFetcher = (
            dependencies.guide_fetcher or MaxrollGuideFetcher(config)
        )
        self._resolver: GuideProfileResolver | None = (
            dependencies.guide_profile_resolver
        )
        if dependencies.parser_factory is not None:
            self._parser_factory = dependencies.parser_factory
        else:
            self._resolver = self._resolver or GuideProfileResolver(config)
            self._parser_factory = self._build_parser_factory()
        self._item_data: ItemDataProvider = (
            dependencies.item_data_provider or DataParser()
        )

    def fetch_guides(self, *, force_refresh: bool = False) -> GuideList:
        """Fetch guide metadata via the injected guide fetcher."""
        try:
            guides = self._guide_fetcher.fetch_guides(force_refresh=force_refresh)
        except GuideFetchError as exc:  # pragma: no cover - network/IO failures
            self._logger.exception("Failed to fetch guides from Maxroll")
            msg = f"Failed to fetch guides: {exc}"
            raise ScrapingError(msg, code=1001) from exc
        self._logger.info("Fetched {} guides from Maxroll.", len(guides))
        return guides

    def build_profiles_from_guides(
        self,
        guides: GuideList,
    ) -> tuple[list[ParsedGuideBundle], int]:
        """Parse build guides into structured profile and usage payloads."""
        bundles: list[ParsedGuideBundle] = []
        skipped = 0
        for guide in guides:
            # If we have a resolver available and it reports more than one planner
            # id on the guide page, treat each planner payload as a separate
            # 'sub-guide' and parse them individually. This prevents combining
            # distinct planners (often different classes) into a single Build.
            planner_ids: list[str] | None = None
            if self._resolver is not None:
                try:
                    planner_ids = self._resolver.get_planner_ids(guide.url)
                except Exception:
                    planner_ids = None

            if planner_ids and len(planner_ids) > 1:
                # Expand into per-planner parsing
                for pid in planner_ids:
                    planner_url = (
                        self._config.maxroll_parser.planner_profile_url.format(
                            planner_id=pid
                        )
                    )
                    try:
                        parser = self._parser_factory(planner_url)
                    except (FileNotFoundError, BuildProfileError, ValueError) as exc:
                        extra: dict[str, object] = {
                            "error": repr(exc),
                            "planner_url": planner_url,
                        }
                        if isinstance(exc, BuildProfileError):
                            if exc.file_path:
                                extra["planner_resource"] = exc.file_path
                            if exc.context:
                                extra.update(exc.context)
                        self._logger.exception(
                            "Failed to instantiate parser for planner {}",
                            planner_url,
                            extra=extra,
                        )
                        skipped += 1
                        continue
                    try:
                        profiles = parser.profiles
                        usages = parser.extract_usages()
                    except (BuildProfileError, ValueError, TypeError) as exc:
                        extra: dict[str, object] = {
                            "planner_url": planner_url,
                            "error": str(exc),
                        }
                        if isinstance(exc, BuildProfileError):
                            if exc.file_path:
                                extra["planner_resource"] = exc.file_path
                            if exc.context:
                                extra.update(exc.context)
                        self._logger.exception(
                            "Failed to parse build profile for planner",
                            extra=extra,
                        )
                        skipped += 1
                        continue
                    if not profiles:
                        self._logger.warning(
                            "Skipping planner {} because no profiles were extracted.",
                            planner_url,
                        )
                        skipped += 1
                        continue
                    # Construct a synthetic GuideInfo to keep track of this planner
                    from d3_item_salvager.maxroll_parser.types import GuideInfo

                    subguide = GuideInfo(
                        name=f"{guide.name} (planner {pid})", url=planner_url
                    )
                    bundles.append(
                        ParsedGuideBundle(
                            guide=subguide,
                            profiles=tuple(profiles),
                            usages=tuple(usages),
                        )
                    )
                continue

            # Fallback: single planner or no resolver available — existing behaviour
            try:
                parser = self._parser_factory(guide.url)
            except (FileNotFoundError, BuildProfileError, ValueError) as exc:
                extra: dict[str, object] = {"error": repr(exc), "guide_url": guide.url}
                if isinstance(exc, BuildProfileError):
                    if exc.file_path:
                        extra["planner_resource"] = exc.file_path
                    if exc.context:
                        extra.update(exc.context)
                planner_hint = ""
                if isinstance(exc, BuildProfileError) and exc.file_path:
                    planner_hint = f" ({exc.file_path})"
                self._logger.exception(
                    "Failed to instantiate parser for guide {}{}",
                    guide.url,
                    planner_hint,
                    extra=extra,
                )
                skipped += 1
                continue
            try:
                profiles = parser.profiles
                usages = parser.extract_usages()
            except (BuildProfileError, ValueError, TypeError) as exc:
                extra: dict[str, object] = {"guide_url": guide.url, "error": str(exc)}
                if isinstance(exc, BuildProfileError):
                    if exc.file_path:
                        extra["planner_resource"] = exc.file_path
                    if exc.context:
                        extra.update(exc.context)
                self._logger.exception(
                    "Failed to parse build profile for guide",
                    extra=extra,
                )
                skipped += 1
                continue
            if not profiles:
                self._logger.warning(
                    "Skipping guide {} because no profiles were extracted.", guide.url
                )
                skipped += 1
                continue
            bundles.append(
                ParsedGuideBundle(
                    guide=guide,
                    profiles=tuple(profiles),
                    usages=tuple(usages),
                )
            )
        return bundles, skipped

    def sync_profiles_to_database(
        self,
        bundles: Sequence[ParsedGuideBundle],
    ) -> BuildSyncSummary:
        """Persist parsed build profile data into the database."""
        builds_created = 0
        profiles_created = 0
        items_created = 0
        usages_created = 0

        for bundle in bundles:
            result = self._sync_bundle(bundle)
            builds_created += result.builds_created
            profiles_created += result.profiles_created
            items_created += result.items_created
            usages_created += result.usages_created

        return BuildSyncSummary(
            guides_processed=len(bundles),
            guides_skipped=0,
            builds_created=builds_created,
            profiles_created=profiles_created,
            items_created=items_created,
            usages_created=usages_created,
        )

    def prepare_database(self, *, force_refresh: bool = False) -> BuildSyncSummary:
        """Orchestrate fetching, parsing, and database synchronization."""
        is_production = bool(getattr(self._config, "is_production", False))
        refresh_cache = force_refresh or is_production
        if refresh_cache and not force_refresh and is_production:
            self._logger.info(
                "Production mode detected; forcing a fresh guide fetch to bypass cached data."
            )
        guides = self.fetch_guides(force_refresh=refresh_cache)
        if not guides:
            return BuildSyncSummary(0, 0, 0, 0, 0, 0)

        bundles, skipped = self.build_profiles_from_guides(guides)
        summary = self.sync_profiles_to_database(bundles)
        return BuildSyncSummary(
            guides_processed=len(guides),
            guides_skipped=skipped,
            builds_created=summary.builds_created,
            profiles_created=summary.profiles_created,
            items_created=summary.items_created,
            usages_created=summary.usages_created,
        )

    def _sync_bundle(self, bundle: ParsedGuideBundle) -> BundleSyncResult:
        """Persist a single parsed bundle and return persistence counters."""
        with self._session_scope() as session:
            build, created = self._get_or_create_build(bundle.guide, session)

            profile_payload = self._convert_profiles(bundle.profiles)
            new_profiles = self._insert_profiles_if_needed(
                build.id, profile_payload, session
            )

            profile_map = self._map_profiles_by_name(build.id, session)
            usages = self._prepare_item_usages(bundle.usages, profile_map)

            required_item_ids = {usage.item_id for usage in usages}
            added_items, available_items = self._insert_missing_items(
                required_item_ids, session
            )

            new_usages = self._insert_item_usages(usages, available_items, session)

        return BundleSyncResult(
            builds_created=int(created),
            profiles_created=new_profiles,
            items_created=added_items,
            usages_created=new_usages,
        )

    def _build_parser_factory(self) -> ParserFactory:
        resolver = self._resolver

        def factory(path: str) -> BuildProfileParser:
            return BuildProfileParser(
                path,
                resolver=resolver,
                config=self._config,
            )

        return factory

    @contextmanager
    def _session_scope(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _get_or_create_build(
        self,
        guide: GuideInfo,
        session: Session,
    ) -> tuple[Build, bool]:
        existing = session.exec(
            select(Build).where(Build.url == guide.url)
        ).one_or_none()
        if existing:
            if existing.title != guide.name:
                existing.title = guide.name
                session.add(existing)
                session.commit()
            return existing, False

        insert_build(
            build_id=None, build_title=guide.name, build_url=guide.url, session=session
        )
        created = session.exec(select(Build).where(Build.url == guide.url)).one()
        return created, True

    def _convert_profiles(
        self,
        profiles: BuildProfilePayload,
    ) -> list[Profile]:
        return [
            Profile(name=profile.name, class_name=profile.class_name, build_id=0)
            for profile in profiles
            if profile.name and profile.class_name
        ]

    def _insert_profiles_if_needed(
        self,
        build_id: int | None,
        profiles: Sequence[Profile],
        session: Session,
    ) -> int:
        if build_id is None or not profiles:
            return 0

        existing_profiles = session.exec(
            select(Profile).where(Profile.build_id == build_id)
        ).all()
        existing_names = {profile.name.lower() for profile in existing_profiles}

        new_profiles = [
            Profile(name=profile.name, class_name=profile.class_name, build_id=build_id)
            for profile in profiles
            if profile.name.lower() not in existing_names
        ]
        if not new_profiles:
            return 0

        insert_profiles(new_profiles, build_id, session)
        return len(new_profiles)

    def _map_profiles_by_name(
        self,
        build_id: int | None,
        session: Session,
    ) -> dict[str, Profile]:
        if build_id is None:
            return {}
        profiles = session.exec(
            select(Profile).where(Profile.build_id == build_id)
        ).all()
        return {profile.name.lower(): profile for profile in profiles}

    def _prepare_item_usages(
        self,
        usages: BuildItemUsagePayload,
        profile_map: dict[str, Profile],
    ) -> list[ItemUsage]:
        prepared: list[ItemUsage] = []
        for usage in usages:
            profile = profile_map.get(usage.profile_name.lower())
            if profile is None or profile.id is None:
                self._logger.warning(
                    "Skipping item usage for unknown profile '{}' .", usage.profile_name
                )
                continue
            prepared.append(
                ItemUsage(
                    profile_id=profile.id,
                    item_id=usage.item_id,
                    slot=usage.slot.value,
                    usage_context=usage.usage_context.value,
                )
            )
        return prepared

    def _insert_missing_items(
        self,
        item_ids: set[str],
        session: Session,
    ) -> tuple[int, set[str]]:
        if not item_ids:
            return 0, set()
        item_id_column = cast("InstrumentedAttribute[str]", Item.id)
        existing_ids = set(
            session.exec(
                select(item_id_column).where(item_id_column.in_(item_ids))
            ).all()
        )
        missing_ids = {item_id for item_id in item_ids if item_id not in existing_ids}
        if not missing_ids:
            return 0, existing_ids

        item_payload: dict[str, dict[str, str]] = {}
        for item_id in missing_ids:
            meta: ItemMeta | None = self._item_data.get_item(item_id)
            if meta is None or not (meta.name and meta.type and meta.quality):
                self._logger.warning(
                    "Skipping item '{}' due to incomplete metadata", item_id
                )
                continue
            item_payload[item_id] = {
                "id": meta.id,
                "name": meta.name,
                "type": meta.type,
                "quality": meta.quality,
            }
        if not item_payload:
            return 0, existing_ids

        insert_items_from_dict(item_payload, session)
        return len(item_payload), existing_ids | set(item_payload.keys())

    def _insert_item_usages(
        self,
        usages: list[ItemUsage],
        available_items: set[str],
        session: Session,
    ) -> int:
        if not usages:
            return 0
        profile_ids = {usage.profile_id for usage in usages}
        existing_keys: set[tuple[int | None, str, str, str]] = set()
        if profile_ids:
            profile_id_column = cast(
                "InstrumentedAttribute[int | None]", ItemUsage.profile_id
            )
            existing_usages = session.exec(
                select(ItemUsage).where(profile_id_column.in_(profile_ids))
            ).all()
            existing_keys = {
                (usage.profile_id, usage.item_id, usage.slot, usage.usage_context)
                for usage in existing_usages
            }
        new_usages: list[ItemUsage] = []
        for usage in usages:
            key = (usage.profile_id, usage.item_id, usage.slot, usage.usage_context)
            if usage.item_id not in available_items:
                self._logger.warning(
                    "Omitting usage for unavailable item '{}'.", usage.item_id
                )
                continue
            if key in existing_keys:
                continue
            new_usages.append(usage)
        if not new_usages:
            return 0
        insert_item_usages_with_validation(new_usages, session)
        return len(new_usages)
