"""CLI entry point for d3_item_salvager. Initializes logging and runs main logic."""

from d3_item_salvager.config.settings import AppConfig, get_config
from d3_item_salvager.logging.setup import setup_logger


def main(app_config: AppConfig | None = None) -> None:
    """
    Main application entry point. Accepts optional AppConfig for DI.

    Args:
        app_config: Optional AppConfig instance for dependency injection.

    Returns:
        None
    """
    if app_config is None:
        app_config = get_config()
    setup_logger(app_config)
    print("Logger initialized. Ready to run application.")
    # Application logic goes here


if __name__ == "__main__":
    main()
