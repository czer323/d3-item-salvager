# Diablo 3 Item Salvager - Maxroll Parser Module

## Maxroll Parser Overview

This module is responsible for fetching, parsing, and caching data from Maxroll.gg. It is designed to be a self-contained unit that can be used to retrieve information about Diablo 3 build guides, items, and profiles. The primary entry point for this module is the `MaxrollClient` class, which provides a simplified interface for all the module's capabilities.

The internal components of this module (parsers, cache, etc.) are encapsulated and managed by the `MaxrollClient`, providing a clean and simple public API.

## MaxrollClient Usage

The `MaxrollClient` is the recommended way to interact with this module. It acts as a facade, simplifying access to the underlying components.

First, instantiate the client with an `AppConfig` object:

```python
from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.maxroll_parser import MaxrollClient

# Assume config is loaded appropriately
config = AppConfig()
client = MaxrollClient(config)
```

### Fetching Guides

To get a list of all available build guides:

```python
# Returns a list of GuideInfo objects
guides = client.get_guides()

for guide in guides:
    print(f"- {guide.name}: {guide.url}")
```

### Parsing Build Profiles

To parse a build profile from a local JSON file. The client will cache the parsed profiles in memory to avoid re-parsing the same file.

```python
# Provide the path to a build profile JSON file
# This file is not included in the repository and must be acquired separately.
# You can use one of the files from the `reference` directory for testing.
profile_file_path = "reference/profile_object_861723133.json"

# Returns a list of BuildProfileData objects
profiles = client.get_build_profiles(profile_file_path)

for profile in profiles:
    print(f"- Profile: {profile.name} (Class: {profile.class_name})")
```

### Retrieving Item Usages from a Profile

To get a structured list of all items used in a build profile, you can use the `get_item_usages` method. This is the most direct way to get the data needed to determine which items are required for a build.

```python
# Returns a list of BuildProfileItems objects
item_usages = client.get_item_usages(profile_file_path)

print(f"Found {len(item_usages)} item usages in the profile.")
for usage in item_usages:
    print(
        f"- Item: {usage.item_id} (Slot: {usage.slot}, Context: {usage.usage_context})"
    )
```

### Retrieving Item Data

You can retrieve metadata for a single item by its ID, or get all items at once. The item data is loaded once and reused across all calls.

**Get a single item:**

```python
# The item ID for "Bane of the Trapped"
item_id = "Unique_Gem_002_x1"

# Returns an ItemMeta object or None
item = client.get_item_data(item_id)

if item:
    print(f"Item Found: {item.name} (Type: {item.type}, Quality: {item.quality})")
```

**Get all items:**

```python
# Returns a mapping of item_id -> ItemMeta
all_items = client.get_all_items()

print(f"Total items loaded: {len(all_items)}")
# Example: Accessing an item from the returned dictionary
# Note: The item ID for "The Furnace" is "Unique_Mace_2H_104_x1"
the_furnace = all_items.get("Unique_Mace_2H_104_x1")
if the_furnace:
    print(f"Found The Furnace: {the_furnace.name}")
```

## Discrepancies

- The `MaxrollGuideFetcher` has a `_fetch_from_file` method that is only used if the `api_url` is a local file path. This is a bit of a code smell. It would be better to have a separate class for fetching from a file, or to use a more generic approach that can handle both local and remote files.
- The `maxroll_exceptions.py` file defines a custom exception hierarchy, which is good. However, the exceptions in the rest of the `d3_item_salvager` application inherit from a different `BaseError`. It would be better to have a single exception hierarchy for the entire application.
