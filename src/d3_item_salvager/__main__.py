"""CLI entry point for d3_item_salvager. Initializes logging and runs main logic."""

from d3_item_salvager.logging.setup import setup_logger


def main() -> None:
    """Main application entry point."""
    print("Logger initialized. Ready to run application.")
    # Application logic goes here


if __name__ == "__main__":
    setup_logger()
    main()
