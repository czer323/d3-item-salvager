"""Query and filter logic for Diablo 3 Item Salvager database."""

from collections.abc import Sequence

from sqlmodel import Session, select

from src.d3_item_salvager.data.models import Item, ItemUsage, Profile


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
