"""CLI entry point for d3_item_salvager. Initializes logging and runs main logic."""

from dependency_injector.wiring import Provide, inject

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.container import Container
from d3_item_salvager.logging.setup import setup_logger


@inject
def main(app_config: AppConfig = Provide[Container.config]) -> None:
    """
    Main application entry point. Accepts optional AppConfig for DI.

    Args:
        app_config: Optional AppConfig instance for dependency injection.

    Returns:
        None
    """
    setup_logger(app_config)
    print("Logger initialized. Ready to run application.")
    # Application logic goes here


if __name__ == "__main__":
    container = Container()
    container.wire(modules=[__name__])  # pylint: disable=no-member
    main()
