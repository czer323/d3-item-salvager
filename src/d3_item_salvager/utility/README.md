# Diablo 3 Item Salvager - Utility Module

## Utility Overview

This module contains various utility scripts that are not part of the main application logic but are useful for development and data management.

### Scripts

- **`extract_item_types.py`**: A script to extract and print all unique item types from the `reference/data.json` file. This is useful for debugging and for keeping the `allowed_types` list in `src/d3_item_salvager/data/loader.py` up to date.
- **`load_reference_data.py`**: A script to load reference data into the database. It reads data from the `reference` directory and uses the `DataParser` and `BuildProfileParser` to insert the data into the database.

### Usage

The scripts in this module are intended to be run from the command line. For example, to run the `extract_item_types.py` script, you can use the following command:

```bash
python -m d3_item_salvager.utility.extract_item_types
```

## Discrepancies

- The `load_reference_data.py` script has a hardcoded path to the `profile_object_861723133.json` file. This is not ideal as it makes it difficult to load other profile files. It would be better to pass the file path as a command-line argument.
- The `load_items` function in `load_reference_data.py` is commented out in the `main` function. This means that items are not loaded by default when the script is run.
- The `insert_build_and_profiles` function in `load_reference_data.py` has a lot of logic. It would be better to break it down into smaller, more manageable functions.
- The scripts in this module use `loguru` for logging, but they also print to the console. It would be better to use the logger for all output.
- The `extract_item_types.py` script uses a hardcoded path to the `data.json` file. It would be better to get this path from the application configuration.
- The `__init__.py` file is empty, which is fine, but it could be used to expose the utility functions to other modules if needed.
