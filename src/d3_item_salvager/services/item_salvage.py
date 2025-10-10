"""Business logic for item salvage operations."""

from dataclasses import dataclass

from sqlmodel import Session

from d3_item_salvager.config.settings import AppConfig
from d3_item_salvager.services.protocols import ServiceLogger


@dataclass(frozen=True, slots=True)
class ItemSalvageDependencies:
    """Immutable dependencies required by :class:`ItemSalvageService`."""

    session: Session
    config: AppConfig
    logger: ServiceLogger


class ItemSalvageService:  # pylint: disable=too-few-public-methods
    """Encapsulate item salvage workflows (pending implementation)."""

    def __init__(self, dependencies: ItemSalvageDependencies) -> None:
        self._session = dependencies.session
        self._config = dependencies.config
        self._logger = dependencies.logger

    def salvage_item(self, item_id: str) -> dict[str, str]:
        """Entry point for salvaging an item by ID.

        The concrete salvage workflow has not been implemented yet. When invoked,
        this method logs the attempted operation and raises ``NotImplementedError``
        to signal the missing business rules.
        """
        self._logger.warning(
            "Item salvage requested for %s but is not implemented.", item_id
        )
        message = "Item salvage workflow has not been implemented yet."
        raise NotImplementedError(message)
