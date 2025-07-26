"""Models for Diablo 3 Item Salvager"""

from sqlmodel import Field, Relationship, SQLModel


class Build(SQLModel, table=True):
    """Represents a Diablo 3 build guide.

    Attributes:
        id: Primary key for the build.
        title: Title of the build guide.
        url: URL of the build guide.
    """

    id: int | None = Field(default=None, primary_key=True)
    title: str
    url: str
    profiles: list["Profile"] = Relationship(back_populates="build")


class Profile(SQLModel, table=True):
    """Represents a variant/profile of a build.

    Attributes:
        id: Primary key for the profile.
        build_id: Foreign key to the associated build.
        name: Name of the profile/variant.
        class_name: Character class for the profile.
    """

    id: int | None = Field(default=None, primary_key=True)
    build_id: int = Field(foreign_key="build.id")
    name: str
    class_name: str = Field(index=True)
    build: Build | None = Relationship(back_populates="profiles")
    usages: list["ItemUsage"] = Relationship(back_populates="profile")


class Item(SQLModel, table=True):
    """Represents an item from the master item list.

    Attributes:
        id: Unique item identifier.
        name: Name of the item.
        type: Item type, correlates to slot (e.g., weapon, ring).
        quality: Rarity or set/legendary status.
    """

    id: str = Field(primary_key=True)
    name: str
    type: str  # 'type' directly correlates to the 'slot' concept in builds and item usage.
    quality: str
    usages: list["ItemUsage"] = Relationship(back_populates="item")


class ItemUsage(SQLModel, table=True):
    """Represents the usage of an item in a build/profile.

    Attributes:
        id: Primary key for the item usage.
        profile_id: Foreign key to the associated profile.
        item_id: Foreign key to the associated item.
        slot: Equipment slot for the item.
        usage_context: How the item is used (main, follower, kanai).
    """

    id: int | None = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key="profile.id", index=True)
    item_id: str = Field(foreign_key="item.id", index=True)
    slot: str = Field(index=True)
    usage_context: str = Field(index=True)
    profile: Profile | None = Relationship(back_populates="usages")
    item: Item | None = Relationship(back_populates="usages")
