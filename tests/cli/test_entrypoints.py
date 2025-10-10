"""Tests reproducing CLI entrypoint failures."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from d3_item_salvager.__main__ import app_cli, run_cli, run_workers
from d3_item_salvager.container import Container


def test_container_instantiation_raises_validation_error() -> None:
    """Creating the DI Container without overrides should raise ValidationError.

    This reproduces the failure observed when invoking the CLI: Container() tries to
    construct AppConfig and pydantic raises a ValidationError because required
    fields (e.g. 'maxroll_parser') are missing.
    """
    # Calling the provider forces AppConfig construction and should raise
    container = Container()
    with pytest.raises(ValidationError, match="maxroll_parser"):
        # resolve the config provider which constructs AppConfig
        container.config()


def test_run_cli_raises_when_config_missing() -> None:
    """run_cli should raise a ValidationError when AppConfig is not provided."""
    # create and wire container like the CLI does, then call run_cli which will
    # resolve the AppConfig provider and raise ValidationError
    container = Container()
    container.wire(modules=["d3_item_salvager.__main__"])  # mimic CLI wiring
    with pytest.raises(ValidationError, match="maxroll_parser"):
        run_cli()


def test_run_workers_raises_when_config_missing() -> None:
    """run_workers should raise a ValidationError when AppConfig is not provided."""
    container = Container()
    container.wire(modules=["d3_item_salvager.__main__"])  # mimic CLI wiring
    with pytest.raises(ValidationError, match="maxroll_parser"):
        run_workers()


def test_typer_cli_api_subcommand_fails() -> None:
    """Invoking the Typer CLI 'api' subcommand should fail due to missing AppConfig."""
    runner = CliRunner()
    result = runner.invoke(app_cli, ["api"])
    # Typer will print the exception information in exit output; assert non-zero
    assert result.exit_code != 0
    assert "maxroll_parser" in result.output
