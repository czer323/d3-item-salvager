"""CLI entry point for d3_item_salvager. Initializes logging and runs main logic."""

from d3_item_salvager.logging.setup import setup_logger

if __name__ == "__main__":
    setup_logger()
    # TODO: Add main application logic here
    print("Logger initialized. Ready to run application.")
