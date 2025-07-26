"""Initialize the database and create all tables for Diablo 3 Item Salvager."""

from d3_item_salvager.data.db import create_db_and_tables

if __name__ == "__main__":
    create_db_and_tables()
    print("Database and tables created successfully.")
