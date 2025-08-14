# Diablo 3 Item Salvager - Data Module

## Data Overview

This module is responsible for all database interactions. It defines the database schema, provides functions for creating and initializing the database, and contains queries for retrieving data.

### Database Schema

The database schema is defined in `src/d3_item_salvager/data/models.py` using `sqlmodel`. The following models are defined:

- `Build`: Represents a Diablo 3 build guide.
- `Profile`: Represents a variant/profile of a build.
- `Item`: Represents an item from the master item list.
- `ItemUsage`: Represents the usage of an item in a build/profile.

### Database Setup

The database engine and session setup are handled by the dependency injection container. The `create_db_and_tables` function in `src/d3_item_salvager/data/db.py` is used to create the database and tables.

To initialize the database, you can run the `init_db.py` script:

```bash
python -m d3_item_salvager.data.init_db
```

### Data Loading

The `src/d3_item_salvager/data/loader.py` file contains functions for inserting data into the database. These functions are used to populate the database with data from the Maxroll parser.

### Queries

The `src/d3_item_salvager/data/queries.py` file contains functions for querying the database. These functions provide a convenient way to retrieve data from the database without writing raw SQL queries.

## Discrepancies

- The `loader.py` file contains a hardcoded list of `allowed_types` and `allowed_qualities`. This is not ideal as it can become out of sync with the data from the Maxroll parser. It would be better to load these values from a configuration file or from the database.
- The `loader.py` functions print to the console instead of using the logging module. This makes it difficult to capture and analyze the output in a production environment.
- The `insert_item_usages_with_validation` function in `loader.py` has a potential performance issue. It fetches the profile and item for each usage individually, which can lead to a large number of database queries. It would be more efficient to fetch all required profiles and items in a single query.
- The join conditions in `queries.py` are redundant. `join(ItemUsage)` on a relationship already implies the join condition. The explicit `.where(Item.id == ItemUsage.item_id)` is not necessary.
- The `init_db.py` script uses a relative import `from d3_item_salvager.container import Container`. This can cause issues when running the script from different directories. It would be better to use an absolute import.
