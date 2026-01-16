"""Query and filter logic for Diablo 3 Item Salvager database."""

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from sqlalchemy import func
from sqlmodel import Session, select

from d3_item_salvager.data.models import Build, Item, ItemUsage, Profile

if TYPE_CHECKING:
    from sqlalchemy.orm import InstrumentedAttribute


def get_items_by_class(session: Session, class_name: str) -> Sequence[Item]:
    """Fetch all items used by profiles of a given class."""
    statement = (
        select(Item)
        .join(ItemUsage)
        .join(Profile)
        .where(Item.id == ItemUsage.item_id)
        .where(ItemUsage.profile_id == Profile.id)
        .where(Profile.class_name == class_name)
    )
    return session.exec(statement).all()


def get_items_by_build(session: Session, build_id: int) -> Sequence[Item]:
    """Fetch all items used in a specific build."""
    statement = (
        select(Item)
        .join(ItemUsage)
        .join(Profile)
        .where(Item.id == ItemUsage.item_id)
        .where(ItemUsage.profile_id == Profile.id)
        .where(Profile.build_id == build_id)
    )
    return session.exec(statement).all()


def get_item_usages_by_slot(session: Session, slot: str) -> Sequence[ItemUsage]:
    """Fetch all item usages for a given slot (e.g., 'mainhand', 'helm')."""
    statement = select(ItemUsage).where(ItemUsage.slot == slot)
    return session.exec(statement).all()


def get_item_usages_by_context(
    session: Session, usage_context: str
) -> Sequence[ItemUsage]:
    """Fetch all item usages for a given usage context (e.g., 'main', 'follower', 'kanai')."""
    statement = select(ItemUsage).where(ItemUsage.usage_context == usage_context)
    return session.exec(statement).all()


def get_profiles_for_build(session: Session, build_id: int) -> Sequence[Profile]:
    """Fetch all profiles for a given build."""
    statement = select(Profile).where(Profile.build_id == build_id)
    return session.exec(statement).all()


def get_item_usages_for_profile(
    session: Session, profile_id: int
) -> Sequence[ItemUsage]:
    """Fetch all item usages for a given profile."""
    statement = select(ItemUsage).where(ItemUsage.profile_id == profile_id)
    return session.exec(statement).all()


def get_items_for_profile(session: Session, profile_id: int) -> Sequence[Item]:
    """Fetch all items used in a given profile."""
    statement = (
        select(Item)
        .join(ItemUsage)
        .where(Item.id == ItemUsage.item_id)
        .where(ItemUsage.profile_id == profile_id)
    )
    return session.exec(statement).all()


def get_all_items(session: Session) -> Sequence[Item]:
    """Fetch all items from the database."""
    statement = select(Item)
    items = session.exec(statement).all()
    return items


def get_all_item_usages(session: Session) -> Sequence[ItemUsage]:
    """Fetch all item usages from the database."""
    statement = select(ItemUsage)
    usages = session.exec(statement).all()
    return usages


def get_item_usages_with_names(session: Session) -> Sequence[tuple[ItemUsage, str]]:
    """Fetch all item usages and their associated item names."""
    statement = select(ItemUsage, Item.name).join(Item)
    results = session.exec(statement).all()
    return results


def list_items(
    session: Session,
    *,
    class_name: str | None = None,
    slot: str | None = None,
    set_status: str | None = None,
    usage_context: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[Item], int]:
    """Return filtered items with pagination metadata."""
    statement = select(Item)

    if class_name or slot or usage_context:
        statement = statement.join(ItemUsage)
    if class_name:
        statement = statement.join(Profile)
        statement = statement.where(Profile.class_name == class_name)
    if slot:
        statement = statement.where(ItemUsage.slot == slot)
    if usage_context:
        statement = statement.where(ItemUsage.usage_context == usage_context)
    if set_status:
        statement = statement.where(Item.quality == set_status)

    statement = statement.distinct().order_by(Item.name)
    count_statement = select(func.count()).select_from(statement.subquery())

    total = session.exec(count_statement).one()
    items = session.exec(statement.offset(offset).limit(limit)).all()
    return items, total


def get_item_usage_classes(session: Session, item_id: str) -> list[str]:
    """Return distinct class names that use the given item (filter out nulls)."""
    statement = (
        select(Profile.class_name)
        .join(ItemUsage)
        .where(ItemUsage.profile_id == Profile.id)
        .where(ItemUsage.item_id == item_id)
        .distinct()
    )
    # Return distinct class names; DB adapters will normally return strings here
    return [str(r) for r in session.exec(statement).all()]


def get_usage_classes_for_items(
    session: Session, item_ids: Sequence[str]
) -> dict[str, list[str]]:
    """Return a mapping of item_id -> list[class_name] for all provided item ids in one query."""
    if not item_ids:
        return {}
    statement = (
        select(ItemUsage.item_id, Profile.class_name)
        .join(Profile)
        .where(ItemUsage.profile_id == Profile.id)
        .distinct()
    )
    rows = session.exec(statement).all()
    # Filter rows in Python to avoid SQLAlchemy attribute type issues in static analysis
    rows = [r for r in rows if r[0] in set(item_ids)]
    mapping: dict[str, list[str]] = {}
    for item_id, class_name in rows:
        mapping.setdefault(item_id, []).append(str(class_name))
    # Deduplicate and sort class lists for deterministic order
    for k, v in mapping.items():
        mapping[k] = sorted(set(v))
    return mapping


def list_builds(
    session: Session,
    *,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[Build], int]:
    """Return builds with pagination metadata.

    Aggregation behavior: When multiple Build rows represent the same logical
    guide (e.g., per-planner expanded builds with titles like
    "Guide Name (planner 123)"), present a single representative Build per
    logical guide. The representative Build's title is normalized by stripping
    a trailing "(planner ...)" suffix and the representative URL prefers a
    non-planner URL when available.
    """
    # Fetch all builds ordered by title so grouping preserves stable ordering
    statement = select(Build).order_by(Build.title)
    rows = session.exec(statement).all()

    from typing import Any

    groups: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}

    def _base_title(title: str) -> str:
        # Remove " (planner XXX)" suffix if present
        return re.sub(r"\s*\(planner.*\)$", "", title).strip()

    for build in rows:
        key = _base_title(build.title).lower()
        if key not in seen:
            seen[key] = {"title": _base_title(build.title), "representative": build}
            groups.append(seen[key])
            continue
        # If we already have a representative that looks like a planner URL,
        # prefer a non-planner URL if we encounter one in the same group.
        rep = seen[key]["representative"]
        rep_url = getattr(rep, "url", "") or ""
        cur_url = getattr(build, "url", "") or ""
        if ("planners." in rep_url or "/profiles/load/" in rep_url) and (
            "planners." not in cur_url and "/profiles/load/" not in cur_url
        ):
            seen[key]["representative"] = build

    total = len(groups)
    selected = groups[offset : offset + limit]

    # Construct lightweight Build objects for the API payload with normalized
    # titles and representative URLs. We create transient Build instances here
    # rather than mutating persisted objects.
    result_builds: list[Build] = []
    for g in selected:
        rep: Build = g["representative"]
        result_builds.append(Build(id=rep.id, title=g["title"], url=rep.url))

    return result_builds, total


def list_profiles(
    session: Session,
    *,
    class_name: str | None = None,
    build_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[Profile], int]:
    """Return profiles filtered by class or build with pagination metadata."""
    statement = select(Profile)
    if class_name:
        statement = statement.where(Profile.class_name == class_name)
    if build_id:
        statement = statement.where(Profile.build_id == build_id)

    statement = statement.order_by(Profile.name)
    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_statement).one()
    profiles = session.exec(statement.offset(offset).limit(limit)).all()
    return profiles, total


def list_item_usages(
    session: Session,
    *,
    profile_id: int | None = None,
    item_id: str | None = None,
    usage_context: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[ItemUsage], int]:
    """Return item usages filtered by optional criteria with pagination metadata."""
    statement = select(ItemUsage)
    if profile_id:
        statement = statement.where(ItemUsage.profile_id == profile_id)
    if item_id:
        statement = statement.where(ItemUsage.item_id == item_id)
    if usage_context:
        statement = statement.where(ItemUsage.usage_context == usage_context)

    profile_id_column = cast("InstrumentedAttribute[int | None]", ItemUsage.profile_id)
    item_id_column = cast("InstrumentedAttribute[str]", ItemUsage.item_id)
    statement = statement.order_by(profile_id_column, item_id_column)
    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_statement).one()
    usages = session.exec(statement.offset(offset).limit(limit)).all()
    return usages, total


def list_build_guides_with_classes(
    session: Session,
) -> Sequence[tuple[Build, str | None]]:
    """Return build guides along with an inferred class name.

    Aggregation behavior: Multiple persisted Build rows that correspond to the
    same logical guide (e.g., planner-derived builds titled "Guide Name
    (planner XXX)") are grouped by their normalized base title. A single
    representative Build is returned per logical guide, and the canonical class
    name is chosen by inspecting all profiles across the grouped builds and
    selecting the most common normalized class.

    This implementation performs a single query that outer-joins Build to
    Profile and performs grouping in Python to avoid N+1 queries.
    """
    from d3_item_salvager.utility.class_names import normalize_class_name

    # Fetch all builds with any associated profile class names in one round-trip
    statement = (
        select(Build, Profile.class_name)
        .join(Profile, isouter=True)
        .order_by(Build.title)
    )
    rows = session.exec(statement).all()

    # Helper to normalize titles by removing trailing "(planner ...)" suffix
    def _base_title(title: str) -> str:
        return re.sub(r"\s*\(planner.*\)$", "", title).strip()

    @dataclass
    class _BuildGroup:
        builds: list[Build]
        classes: list[str]
        rep: Build | None = None

    # Group builds by base title while collecting class names and remembering
    # a representative Build (prefer a non-planner URL when available)
    groups: dict[str, _BuildGroup] = {}

    for build, class_name in rows:
        assert build.id is not None, "Expected persisted Build records with non-None id"
        key = _base_title(build.title).lower()
        entry = groups.setdefault(key, _BuildGroup([], []))
        entry.builds.append(build)
        if class_name:
            entry.classes.append(normalize_class_name(class_name))
        # Determine representative build: prefer a non-planner URL if present
        if entry.rep is None:
            entry.rep = build
        else:
            rep_url = getattr(entry.rep, "url", "") or ""
            cur_url = getattr(build, "url", "") or ""
            if ("planners." in rep_url or "/profiles/load/" in rep_url) and (
                "planners." not in cur_url and "/profiles/load/" not in cur_url
            ):
                entry.rep = build

    results: list[tuple[Build, str | None]] = []

    for key, entry in groups.items():
        rep = entry.rep
        assert rep is not None, "Representative build cannot be None"
        normalized_title = _base_title(rep.title)
        # Construct a transient Build with normalized title to present to API
        rep_build = Build(id=rep.id, title=normalized_title, url=rep.url)
        classes = entry.classes
        if not classes:
            results.append((rep_build, None))
            continue
        most_common_class = Counter(classes).most_common(1)[0][0]
        results.append((rep_build, most_common_class))

    return results


def list_variants_for_build(session: Session, build_id: int) -> Sequence[Profile]:
    """Return profile variants associated with a build.

    Aggregation behavior: If a build appears to be a planner-derived sub-build
    (e.g., title contains "(planner ...)") or there exist other builds with the
    same base title, include profiles from all builds that share the same
    normalized base title so that the UI can present a single unified set of
    variants for a logical guide.
    """
    # First, fetch the build to determine its normalized base title
    build_obj = session.exec(select(Build).where(Build.id == build_id)).one_or_none()
    if build_obj is None:
        return []

    base_title = re.sub(r"\s*\(planner.*\)$", "", build_obj.title).strip()

    # Find all builds whose normalized title equals the base_title
    all_builds = session.exec(select(Build)).all()
    build_ids = [
        b.id
        for b in all_builds
        if re.sub(r"\s*\(planner.*\)$", "", b.title).strip() == base_title
    ]

    if not build_ids:
        return []

    # Use the ORM InstrumentedAttribute for build_id to satisfy static typing
    profile_build_id = cast("InstrumentedAttribute[int]", Profile.build_id)
    statement = (
        select(Profile).where(profile_build_id.in_(build_ids)).order_by(Profile.name)
    )
    return session.exec(statement).all()


def get_variant(session: Session, variant_id: int) -> Profile | None:
    """Return a single profile variant by identifier."""
    statement = select(Profile).where(Profile.id == variant_id)
    return session.exec(statement).one_or_none()


def list_item_usage_with_items(
    session: Session,
    variant_id: int,
) -> Sequence[tuple[ItemUsage, Item]]:
    """Return item usage records for a variant with associated item metadata."""
    item_id_column = cast("InstrumentedAttribute[str]", Item.id)
    usage_item_id = cast("InstrumentedAttribute[str]", ItemUsage.item_id)
    usage_profile_id = cast("InstrumentedAttribute[int]", ItemUsage.profile_id)
    usage_slot = cast("InstrumentedAttribute[str]", ItemUsage.slot)
    usage_id = cast("InstrumentedAttribute[int | None]", ItemUsage.id)
    statement = (
        select(ItemUsage, Item)
        .join(Item, item_id_column == usage_item_id)
        .where(usage_profile_id == variant_id)
        .order_by(usage_slot, usage_id)
    )
    return session.exec(statement).all()
