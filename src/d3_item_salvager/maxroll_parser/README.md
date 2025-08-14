# Diablo 3 Item Salvager - Maxroll Parser Module

## Maxroll Parser Overview

This module is responsible for fetching, parsing, and caching data from Maxroll.gg. It is designed to be a self-contained unit that can be used to retrieve information about Diablo 3 build guides, items, and profiles. The primary entry point for this module is the `MaxrollClient` class, which provides a simplified interface for all the module's capabilities.

### Core Components

- **`MaxrollClient`**: The main entry point for the module. It provides a high-level API for accessing the other components.
- **`MaxrollGuideFetcher`**: Fetches guide metadata from the Maxroll API or a local file.
- **`FileGuideCache`**: A file-based cache for guide metadata with TTL support.
- **`BuildProfileParser`**: Parses Diablo 3 build profile JSON files.
- **`DataParser`**: Parses the `data.json` file, which contains master item data.

### Protocols

The module uses a protocol-driven design to allow for dependency injection and easy testing. The protocols are defined in `src/d3_item_salvager/maxroll_parser/protocols.py`.

### Data Types

The data structures used throughout the module are defined in `src/d3_item_salvager/maxroll_parser/types.py`. These are implemented as dataclasses for type safety and immutability.

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

To parse a build profile from a local JSON file:

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

### Retrieving Item Data

You can retrieve metadata for a single item by its ID, or get all items at once.

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

- The `MaxrollClient` instantiates its own dependencies (`MaxrollGuideFetcher`, `BuildProfileParser`, `DataParser`). This is not ideal for dependency injection and testing. It would be better to inject these dependencies into the `MaxrollClient`'s constructor.
- The `BuildProfileParser` is instantiated with a file path every time `get_build_profiles` is called. This is inefficient if the same file is parsed multiple times. A caching mechanism could be implemented to avoid re-parsing the same file.
- The `DataParser` is instantiated every time `get_item_data` or `get_all_items` is called. This is also inefficient. The `DataParser` should be instantiated once and reused.
- The `MaxrollGuideFetcher` has a `_fetch_from_file` method that is only used if the `api_url` is a local file path. This is a bit of a code smell. It would be better to have a separate class for fetching from a file, or to use a more generic approach that can handle both local and remote files.
- The `maxroll_exceptions.py` file defines a custom exception hierarchy, which is good. However, the exceptions in the rest of the `d3_item_salvager` application inherit from a different `BaseError`. It would be better to have a single exception hierarchy for the entire application.
- The `PluginProtocol` is defined but not used anywhere in the module. It should either be used or removed.
- The `parse_slot` function in `build_profile_parser.py` has a `try...except` block that catches a `ValueError` and returns `ItemSlot.OTHER`. This is a good fallback, but it would be better to log the error so that it can be investigated.
