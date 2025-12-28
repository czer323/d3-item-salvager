"""Query and filter logic for Diablo 3 Item Salvager database."""

from collections import Counter
from collections.abc import Sequence
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


def list_builds(
    session: Session,
    *,
    limit: int = 100,
    offset: int = 0,
) -> tuple[Sequence[Build], int]:
    """Return builds with pagination metadata."""
    statement = select(Build).order_by(Build.title)
    count_statement = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_statement).one()
    builds = session.exec(statement.offset(offset).limit(limit)).all()
    return builds, total


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

    Previous implementation used MIN(Profile.class_name) which could pick a
    lexicographically small value when a build had profiles from multiple classes
    (e.g., a stray 'demonhunter' would mask the intended 'Wizard'). This routine
    now determines the canonical class by inspecting profile values per-build and
    selecting the most common normalized class name. Returns None when no profiles
    exist for a build.
    """
    from d3_item_salvager.utility.class_names import normalize_class_name

    builds = session.exec(select(Build).order_by(Build.title)).all()
    results: list[tuple[Build, str | None]] = []
    for build in builds:
        if build.id is None:
            results.append((build, None))
            continue
        rows = session.exec(
            select(Profile.class_name).where(Profile.build_id == build.id)
        ).all()
        normalized = [normalize_class_name(c) for c in rows if c]
        if not normalized:
            results.append((build, None))
            continue
        counts = Counter(normalized)
        most_common_class = counts.most_common(1)[0][0]
        results.append((build, most_common_class))
    return results


def list_variants_for_build(session: Session, build_id: int) -> Sequence[Profile]:
    """Return profile variants associated with a build."""
    statement = (
        select(Profile).where(Profile.build_id == build_id).order_by(Profile.name)
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
