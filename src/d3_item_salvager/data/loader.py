"""Loader functions for inserting sample data into the Diablo 3 Item Salvager database."""

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from d3_item_salvager.data.db import get_session
from d3_item_salvager.data.models import Build, Item, ItemUsage, Profile


def insert_item_usages_with_validation(usages: list[dict], session: Session) -> None:
    """
    Insert item usages into the database, validating that profile_name and item_id exist.

    Args:
        usages: List of dicts with keys: profile_name, item_id, slot, usage_context.
        session: Active database session.
    """
    errors = []
    success_count = 0
    profile_map = {p.name: p for p in session.exec(select(Profile)).all()}

    for usage in usages:
        profile = profile_map.get(usage["profile_name"])
        if profile is None:
            msg = f"Profile name '{usage['profile_name']}' does not exist."
            raise ValueError(msg)
        item = session.get(Item, usage["item_id"])
        if item is None:
            msg = f"Item ID {usage['item_id']} does not exist."
            raise ValueError(msg)
        assert profile.id is not None, "Profile id cannot be None"
        assert item.id is not None, "Item id cannot be None"
        session.add(
            ItemUsage(
                profile_id=profile.id,
                item_id=item.id,
                slot=usage["slot"],
                usage_context=usage["usage_context"],
            )
        )
        success_count += 1
    try:
        session.commit()
    except SQLAlchemyError as e:
        errors.append(({"commit": "commit"}, str(e)))
    print(f"Inserted {success_count} item usages. {len(errors)} errors.")
    if errors:
        print("Errors:")
        for err in errors:
            print(err)


def insert_items_from_dict(
    item_dict: dict[str, dict[str, str]], session: Session | None = None
) -> None:
    """
    Insert cleaned item data from item_dict into the database.

    Args:
        item_dict: Dict mapping item IDs to cleaned item data (id, name, type, quality).
        session: Optional active database session. If not provided, uses get_session().
    """
    errors: list[tuple[dict[str, str], str]] = []
    success_count = 0
    if session is None:
        with get_session() as session_ctx:
            for item_data in item_dict.values():
                try:
                    validate_item_data(item_data, session_ctx)
                    item = Item(
                        id=item_data["id"],
                        name=item_data["name"],
                        type=item_data["type"],
                        quality=item_data["quality"],
                    )
                    session_ctx.add(item)
                    success_count += 1
                except (ValueError, SQLAlchemyError) as e:
                    errors.append((item_data, str(e)))
            try:
                session_ctx.commit()
            except SQLAlchemyError as e:
                errors.append(({"commit": "commit"}, str(e)))
    else:
        for item_data in item_dict.values():
            try:
                validate_item_data(item_data, session)
                item = Item(
                    id=item_data["id"],
                    name=item_data["name"],
                    type=item_data["type"],
                    quality=item_data["quality"],
                )
                session.add(item)
                success_count += 1
            except ValueError as e:
                errors.append((item_data, str(e)))
                raise
            except SQLAlchemyError as e:
                errors.append((item_data, str(e)))
        try:
            session.commit()
        except SQLAlchemyError as e:
            errors.append(({"commit": "commit"}, str(e)))
    print(f"Inserted {success_count} items. {len(errors)} errors.")
    if errors:
        print("Errors:")
        for err in errors:
            print(err)


def validate_item_data(item_data: dict[str, str], session: Session) -> None:
    """
    Validate item data for required fields, allowed values, and duplicates.
    Raises ValueError if validation fails.
    """
    for field in ("id", "name", "type", "quality"):
        if not item_data.get(field):
            msg = f"Missing required field '{field}' in item data: {item_data}"
            raise ValueError(msg)
    # All known types from reference data.json. Filtering may be unnecessary if all types are valid.
    allowed_types = {
        "amulet",
        "ancientblade",
        "archonstaff",
        "axe",
        "axe2h",
        "ballista",
        "battlecestus",
        "belt",
        "boneknife",
        "boots",
        "bow",
        "bracers",
        "caduceus",
        "ceremonialknife",
        "championsword",
        "chestarmor",
        "cinquedeas",
        "cloak",
        "colossusblade",
        "crossbow",
        "crusadershield",
        "dagger",
        "daibo",
        "enchantressfocus",
        "fistweapon",
        "flail",
        "flail1",
        "flail2h",
        "flyingaxe",
        "gloves",
        "gravewand",
        "greatertalons",
        "handcrossbow",
        "helm",
        "hydrabow",
        "hyperionspear",
        "legendspike",
        "lessershard",
        "mace",
        "mace2h",
        "mightybelt",
        "mightyscepter",
        "mightyweapon",
        "mightyweapon2h",
        "mojo",
        "pants",
        "phylactery",
        "polearm",
        "primeshard",
        "quiver",
        "repeatingcrossbow",
        "ring",
        "scoundreltoken",
        "scythe",
        "scythe1",
        "scythe2h",
        "shield",
        "shoulders",
        "source",
        "spear",
        "spiritstone",
        "staff",
        "swirlingcrystal",
        "sword",
        "sword2h",
        "templarrelic",
        "voodoomask",
        "wand",
        "wizardhat",
        "wristsword",
    }
    allowed_qualities = {"set", "legendary", "rare", "magic", "common"}
    if item_data["type"].lower() not in allowed_types:
        msg = (
            f"Invalid item type '{item_data['type']}' for item ID '{item_data['id']}.'"
        )
        raise ValueError(msg)
    if item_data["quality"].lower() not in allowed_qualities:
        msg = f"Invalid item quality '{item_data['quality']}' for item ID '{item_data['id']}.'"
        raise ValueError(msg)
    existing: Item | None = session.get(Item, item_data["id"])
    if existing:
        msg = f"Duplicate item ID '{item_data['id']}' detected."
        print(msg)
        raise ValueError(msg)


def insert_build(
    build_id: int | None, build_title: str, build_url: str, session: Session
) -> None:
    """
    Insert a Build record into the database.

    Args:
        build_id: Unique build ID (can be None for auto-increment).
        build_title: Title of the build.
        build_url: URL or source path for the build.
        session: Active database session.
    """
    build = Build(id=build_id, title=build_title, url=build_url)
    session.add(build)
    session.commit()
    print(f"Inserted build: {build_title} (ID: {build.id})")


def insert_profiles(profiles: list[dict], build_id: int, session: Session) -> None:
    """
    Insert Profile records for a given build into the database.

    Args:
        profiles: List of dicts with profile data (name, class_name, etc.).
        build_id: The build ID to associate with each profile.
        session: Active database session.
    """
    errors = []
    success_count = 0
    for profile_data in profiles:
        name = profile_data.get("name", "Unknown Profile")
        class_name = profile_data.get("class_name", "Unknown Class")
        profile = Profile(build_id=build_id, name=name, class_name=class_name)
        session.add(profile)
        success_count += 1
    try:
        session.commit()
    except SQLAlchemyError as e:
        errors.append(({"commit": "commit"}, str(e)))
    print(
        f"Inserted {success_count} profiles for build {build_id}. {len(errors)} errors."
    )
    if errors:
        print("Errors:")
        for err in errors:
            print(err)
