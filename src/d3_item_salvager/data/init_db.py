"""Initialize the database and create all tables for Diablo 3 Item Salvager."""

from d3_item_salvager.container import Container
from d3_item_salvager.data.db import create_db_and_tables

if __name__ == "__main__":
    container = Container()
    engine = container.engine()
    create_db_and_tables(engine)
    print("Database and tables created successfully.")
