from sqlmodel import select

from d3_item_salvager.data.db import get_session
from d3_item_salvager.data.queries import Item, ItemUsage, Profile

with get_session() as session:
    statement = (
        select(Item)
        .join(ItemUsage)
        .join(Profile)
        .where(Item.id == ItemUsage.item_id)
        .where(ItemUsage.profile_id == Profile.id)
        .where(ItemUsage.usage_context == "kanai")
        .where(Profile.class_name == "necromancer")
    )
    necro_cube_items = session.exec(statement).all()
    # Deduplicate by item id
    seen = set()
    for item in necro_cube_items:
        if item.id not in seen:
            print(f"name='{item.name}' type='{item.type}'")
            seen.add(item.id)
