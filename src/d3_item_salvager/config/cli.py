"""CLI arg parsing using Typer."""

import typer


def main(
    db_url: str = typer.Option(
        "sqlite:///d3_items.db", help="Database connection string"
    ),
    scraper_user_agent: str = typer.Option(
        "Mozilla/5.0", help="Scraper HTTP User-Agent"
    ),
    scraper_timeout: int = typer.Option(10, help="Scraper timeout in seconds"),
) -> None:
    """Entry point for CLI config overrides. Prints parsed values as a dictionary."""
    overrides = {
        "db_url": db_url,
        "scraper_user_agent": scraper_user_agent,
        "scraper_timeout": scraper_timeout,
    }
    typer.echo(overrides)


if __name__ == "__main__":
    typer.run(main)
