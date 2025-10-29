"""Command-line interface for ProductHuntDB.

This module provides a Typer-based CLI for managing the Product Hunt data pipeline.

Commands:
- sync: Synchronize data from Product Hunt API
- export: Export database to CSV files
- publish: Publish dataset to Kaggle
- status: Show database statistics and status
- verify: Verify API authentication

Example:
    $ producthuntdb sync --full-refresh
    $ producthuntdb export --output-dir ./data
    $ producthuntdb publish
    $ producthuntdb status
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from producthuntdb.config import settings
from producthuntdb.io import DatabaseManager, KaggleManager
from producthuntdb.pipeline import DataPipeline

# Initialize CLI app
app     = typer.Typer(
    name="producthuntdb",
    help="Product Hunt API data sink and Kaggle dataset manager",
    add_completion=False,
)
console = Console()


# =============================================================================
# Helper Functions
# =============================================================================


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO
    """
    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG" if verbose else "INFO",
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
        "{message}",
    )


def run_async(coro):
    """Run async coroutine in event loop.

    Args:
        coro: Coroutine to run

    Returns:
        Result of coroutine execution
    """
    return asyncio.run(coro)


# =============================================================================
# CLI Commands
# =============================================================================


@app.command()
def sync(
    full_refresh: bool = typer.Option(
        False,
        "--full-refresh",
        "-f",
        help="Perform full refresh instead of incremental update",
    ),
    max_pages: Optional[int] = typer.Option(
        None,
        "--max-pages",
        "-n",
        help="Maximum pages to fetch per entity (for testing)",
    ),
    posts_only: bool = typer.Option(
        False,
        "--posts-only",
        help="Only sync posts (skip topics and collections)",
    ),
    topics_only: bool = typer.Option(
        False,
        "--topics-only",
        help="Only sync topics",
    ),
    collections_only: bool = typer.Option(
        False,
        "--collections-only",
        help="Only sync collections",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Synchronize data from Product Hunt API to local database.

    This command fetches data from the Product Hunt GraphQL API and stores it
    in a local SQLite database. It supports both full refreshes and incremental
    updates with a safety margin to avoid missing data.

    Examples:
        # Incremental update (default)
        $ producthuntdb sync

        # Full refresh of all data
        $ producthuntdb sync --full-refresh

        # Sync only posts (for testing)
        $ producthuntdb sync --posts-only --max-pages 5

        # Verbose output
        $ producthuntdb sync -v
    """
    setup_logging(verbose)

    console.print("🚀 [bold cyan]ProductHuntDB Sync[/bold cyan]\n")

    # Show configuration
    console.print(f"📍 Database: [yellow]{settings.database_path}[/yellow]")
    console.print(f"🔑 API Token: [yellow]{settings.redact_token()}[/yellow]")
    console.print(
        f"⚡ Concurrency: [yellow]{settings.max_concurrency}[/yellow]"
    )
    console.print(
        f"📄 Page Size: [yellow]{settings.page_size}[/yellow]"
    )

    if full_refresh:
        console.print("🔄 Mode: [bold yellow]Full Refresh[/bold yellow]")
    else:
        console.print(
            "🔄 Mode: [bold green]Incremental Update[/bold green] "
            f"(safety margin: {settings.safety_minutes} minutes)"
        )

    console.print()

    async def _sync():
        pipeline = DataPipeline()

        try:
            await pipeline.initialize()

            # Verify authentication
            await pipeline.verify_authentication()

            # Sync entities based on flags
            if posts_only:
                stats = await pipeline.sync_posts(full_refresh, max_pages)
                console.print(
                    f"\n✅ [bold green]Synced {stats['posts']} posts "
                    f"({stats['users']} users, {stats['topics']} topics)[/bold green]"
                )

            elif topics_only:
                stats = await pipeline.sync_topics(max_pages)
                console.print(
                    f"\n✅ [bold green]Synced {stats['topics']} topics[/bold green]"
                )

            elif collections_only:
                stats = await pipeline.sync_collections(max_pages)
                console.print(
                    f"\n✅ [bold green]Synced {stats['collections']} collections[/bold green]"
                )

            else:
                # Sync all
                stats = await pipeline.sync_all(full_refresh, max_pages)
                console.print(
                    f"\n✅ [bold green]Synced {stats['total_entities']} total entities[/bold green]"
                )

        except Exception as e:
            console.print(f"\n❌ [bold red]Sync failed: {e}[/bold red]")
            raise typer.Exit(code=1)

        finally:
            pipeline.close()

    run_async(_sync())


@app.command()
def export(
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory to write CSV files (defaults to ./data/export)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Export database to CSV files.

    This command exports all database tables to CSV files in the specified
    output directory. The CSV files can be used for analysis or uploaded to
    Kaggle.

    Examples:
        # Export to default directory (./data/export)
        $ producthuntdb export

        # Export to custom directory
        $ producthuntdb export --output-dir /path/to/output
    """
    setup_logging(verbose)

    console.print("📦 [bold cyan]ProductHuntDB Export[/bold cyan]\n")

    # Use settings.export_dir if output_dir not provided
    output_path = output_dir or settings.export_dir

    console.print(f"📍 Database: [yellow]{settings.database_path}[/yellow]")
    console.print(f"📂 Output: [yellow]{output_path}[/yellow]\n")

    try:
        km = KaggleManager()
        km.export_database_to_csv(output_path)

        console.print(f"\n✅ [bold green]Exported to {output_path}[/bold green]")

    except Exception as e:
        console.print(f"\n❌ [bold red]Export failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def publish(
    data_dir: Optional[Path] = typer.Option(
        None,
        "--data-dir",
        "-d",
        help="Directory containing CSV files (defaults to export then publish)",
    ),
    title: str = typer.Option(
        "ProductHuntDB",
        "--title",
        "-t",
        help="Dataset title",
    ),
    description: str = typer.Option(
        "Product Hunt data extracted via GraphQL API",
        "--description",
        help="Dataset description",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Publish or update Kaggle dataset.

    This command uploads the database export to Kaggle. If the dataset already
    exists, it creates a new version. Otherwise, it creates a new dataset.

    Requires KAGGLE_USERNAME and KAGGLE_KEY to be configured.

    Examples:
        # Export and publish in one step
        $ producthuntdb publish

        # Publish existing export
        $ producthuntdb publish --data-dir ./export
    """
    setup_logging(verbose)

    console.print("📤 [bold cyan]ProductHuntDB Kaggle Publish[/bold cyan]\n")

    if not settings.kaggle_username or not settings.kaggle_key:
        console.print(
            "❌ [bold red]Kaggle credentials not configured![/bold red]\n"
            "Please set KAGGLE_USERNAME and KAGGLE_KEY environment variables."
        )
        raise typer.Exit(code=1)

    if not settings.kaggle_dataset_slug:
        console.print(
            "❌ [bold red]Kaggle dataset slug not configured![/bold red]\n"
            "Please set KAGGLE_DATASET_SLUG in configuration."
        )
        raise typer.Exit(code=1)

    try:
        km = KaggleManager()

        # If no data directory specified, export first
        if not data_dir:
            data_dir = Path("./export")
            console.print(f"📦 Exporting database to {data_dir}...\n")
            km.export_database_to_csv(data_dir)

        console.print(f"📂 Data Directory: [yellow]{data_dir}[/yellow]")
        console.print(f"🏷️  Dataset: [yellow]{settings.kaggle_dataset_slug}[/yellow]\n")

        km.publish_dataset(data_dir, title, description)

        console.print(
            f"\n✅ [bold green]Published to Kaggle: "
            f"https://www.kaggle.com/datasets/{settings.kaggle_dataset_slug}[/bold green]"
        )

    except Exception as e:
        console.print(f"\n❌ [bold red]Publish failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def status(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Show database statistics and pipeline status.

    This command displays current database statistics, including entity counts,
    last sync timestamps, and configuration information.

    Examples:
        $ producthuntdb status
    """
    setup_logging(verbose)

    console.print("📊 [bold cyan]ProductHuntDB Status[/bold cyan]\n")

    try:
        db = DatabaseManager()
        db.initialize()

        # Configuration
        config_table = Table(title="Configuration", show_header=False)
        config_table.add_column("Key", style="cyan")
        config_table.add_column("Value", style="yellow")

        config_table.add_row("Database Path", str(settings.database_path))
        config_table.add_row("GraphQL Endpoint", settings.graphql_endpoint)
        config_table.add_row("API Token", settings.redact_token())
        config_table.add_row("Max Concurrency", str(settings.max_concurrency))
        config_table.add_row("Page Size", str(settings.page_size))
        config_table.add_row("Safety Margin", f"{settings.safety_minutes} minutes")

        if settings.kaggle_dataset_slug:
            config_table.add_row("Kaggle Dataset", settings.kaggle_dataset_slug)

        console.print(config_table)
        console.print()

        # Database statistics
        pipeline = DataPipeline(db=db)
        stats    = pipeline.get_statistics()

        stats_table = Table(title="Database Statistics")
        stats_table.add_column("Entity", style="cyan")
        stats_table.add_column("Count", justify="right", style="green")

        stats_table.add_row("Posts", f"{stats['posts']:,}")
        stats_table.add_row("Users", f"{stats['users']:,}")
        stats_table.add_row("Topics", f"{stats['topics']:,}")
        stats_table.add_row("Collections", f"{stats['collections']:,}")
        stats_table.add_row("Comments", f"{stats['comments']:,}")
        stats_table.add_row("Votes", f"{stats['votes']:,}")

        console.print(stats_table)
        console.print()

        # Crawl state
        posts_state = db.get_crawl_state("posts")
        if posts_state:
            console.print(
                f"📅 Last posts sync: [yellow]{posts_state}[/yellow]"
            )
        else:
            console.print("📅 No sync history found")

        db.close()

    except Exception as e:
        console.print(f"\n❌ [bold red]Status failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def verify(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Verify API authentication and connectivity.

    This command tests the Product Hunt API connection and displays information
    about the authenticated user.

    Examples:
        $ producthuntdb verify
    """
    setup_logging(verbose)

    console.print("🔐 [bold cyan]ProductHuntDB Authentication[/bold cyan]\n")

    console.print(f"🌐 Endpoint: [yellow]{settings.graphql_endpoint}[/yellow]")
    console.print(f"🔑 Token: [yellow]{settings.redact_token()}[/yellow]\n")

    async def _verify():
        pipeline = DataPipeline()

        try:
            await pipeline.initialize()

            viewer = await pipeline.verify_authentication()
            user   = viewer.get("user", {})

            # Display viewer info
            viewer_table = Table(title="Authenticated User", show_header=False)
            viewer_table.add_column("Field", style="cyan")
            viewer_table.add_column("Value", style="green")

            viewer_table.add_row("Username", user.get("username", "N/A"))
            viewer_table.add_row("Name", user.get("name", "N/A"))
            viewer_table.add_row("Headline", user.get("headline", "N/A") or "N/A")
            viewer_table.add_row("URL", user.get("url", "N/A"))

            console.print(viewer_table)
            console.print("\n✅ [bold green]Authentication successful![/bold green]")

            # Get rate limit status
            rate_limit = pipeline.client.get_rate_limit_status()
            if rate_limit.get("remaining"):
                console.print(
                    f"\n📊 Rate Limit: {rate_limit['remaining']}/{rate_limit['limit']} "
                    f"remaining (resets at {rate_limit['reset'] or 'unknown'})"
                )

        except Exception as e:
            console.print(f"\n❌ [bold red]Authentication failed: {e}[/bold red]")
            raise typer.Exit(code=1)

        finally:
            pipeline.close()

    run_async(_verify())


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force re-initialization (recreate database)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Initialize database and verify setup.

    This command initializes the SQLite database, creates all necessary tables,
    and verifies the configuration.

    Examples:
        # Initialize database
        $ producthuntdb init

        # Force re-initialization
        $ producthuntdb init --force
    """
    setup_logging(verbose)

    console.print("🏗️  [bold cyan]ProductHuntDB Initialization[/bold cyan]\n")

    try:
        # Check if database exists
        db_path = Path(str(settings.database_path))
        if db_path.exists() and not force:
            console.print(
                f"⚠️  Database already exists at {settings.database_path}\n"
                "Use --force to recreate it."
            )
            return

        # Initialize database
        db = DatabaseManager()
        db.initialize()

        console.print(f"✅ Database created at [yellow]{settings.database_path}[/yellow]")

        # Show configuration
        console.print("\n📋 Configuration:")
        console.print(f"  • GraphQL Endpoint: {settings.graphql_endpoint}")
        console.print(f"  • Max Concurrency: {settings.max_concurrency}")
        console.print(f"  • Page Size: {settings.page_size}")
        console.print(f"  • Safety Margin: {settings.safety_minutes} minutes")

        db.close()

        console.print("\n✅ [bold green]Initialization complete![/bold green]")
        console.print("\nNext steps:")
        console.print("  1. Set PRODUCTHUNT_TOKEN environment variable")
        console.print("  2. Run: producthuntdb verify")
        console.print("  3. Run: producthuntdb sync")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"\n❌ [bold red]Initialization failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def migrate(
    message: Optional[str] = typer.Option(
        None,
        "--message",
        "-m",
        help="Migration message (autogenerate if not provided)",
    ),
    autogenerate: bool = typer.Option(
        True,
        "--autogenerate/--no-autogenerate",
        help="Automatically detect schema changes",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Create a new database migration.

    This command generates a new Alembic migration script. By default, it
    auto-detects changes in your SQLModel models.

    Examples:
        # Auto-generate migration
        $ producthuntdb migrate

        # Create migration with custom message
        $ producthuntdb migrate --message "add new column"

        # Create empty migration (manual editing required)
        $ producthuntdb migrate --no-autogenerate --message "custom changes"
    """
    import subprocess

    setup_logging(verbose)

    console.print("🔧 [bold cyan]Creating Database Migration[/bold cyan]\n")

    try:
        # Build alembic command
        cmd = ["uv", "run", "alembic", "revision"]

        if autogenerate:
            cmd.append("--autogenerate")

        if message:
            cmd.extend(["-m", message])
        else:
            cmd.extend(["-m", "Auto-generated migration"])

        console.print(f"📝 Command: [yellow]{' '.join(cmd)}[/yellow]\n")

        # Run alembic revision
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        if result.stdout:
            console.print(result.stdout)

        console.print("\n✅ [bold green]Migration created successfully![/bold green]")
        console.print("\n💡 Next steps:")
        console.print("  1. Review the migration file in alembic/versions/")
        console.print("  2. Run: producthuntdb upgrade")

    except subprocess.CalledProcessError as e:
        console.print(f"\n❌ [bold red]Migration creation failed![/bold red]")
        if e.stderr:
            console.print(f"Error: {e.stderr}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n❌ [bold red]Migration creation failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def upgrade(
    revision: str = typer.Argument(
        "head",
        help="Revision to upgrade to (default: head)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Upgrade database to a specific revision.

    This command applies pending migrations to bring the database schema
    up to date.

    Examples:
        # Upgrade to latest version
        $ producthuntdb upgrade

        # Upgrade to specific revision
        $ producthuntdb upgrade abc123
    """
    import subprocess

    setup_logging(verbose)

    console.print("⬆️  [bold cyan]Upgrading Database[/bold cyan]\n")

    try:
        cmd = ["uv", "run", "alembic", "upgrade", revision]

        console.print(f"📝 Command: [yellow]{' '.join(cmd)}[/yellow]\n")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        if result.stdout:
            console.print(result.stdout)

        console.print(f"\n✅ [bold green]Database upgraded to {revision}![/bold green]")

    except subprocess.CalledProcessError as e:
        console.print(f"\n❌ [bold red]Upgrade failed![/bold red]")
        if e.stderr:
            console.print(f"Error: {e.stderr}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n❌ [bold red]Upgrade failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def downgrade(
    revision: str = typer.Argument(
        "-1",
        help="Revision to downgrade to (default: -1 for previous)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Downgrade database to a previous revision.

    This command rolls back migrations to a previous state.

    Examples:
        # Downgrade one revision
        $ producthuntdb downgrade

        # Downgrade to specific revision
        $ producthuntdb downgrade abc123

        # Downgrade to base (empty database)
        $ producthuntdb downgrade base
    """
    import subprocess

    setup_logging(verbose)

    console.print("⬇️  [bold cyan]Downgrading Database[/bold cyan]\n")

    try:
        cmd = ["uv", "run", "alembic", "downgrade", revision]

        console.print(f"📝 Command: [yellow]{' '.join(cmd)}[/yellow]\n")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        if result.stdout:
            console.print(result.stdout)

        console.print(f"\n✅ [bold green]Database downgraded to {revision}![/bold green]")

    except subprocess.CalledProcessError as e:
        console.print(f"\n❌ [bold red]Downgrade failed![/bold red]")
        if e.stderr:
            console.print(f"Error: {e.stderr}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n❌ [bold red]Downgrade failed: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def migration_history(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Show database migration history.

    This command displays the current database revision and migration history.

    Example:
        $ producthuntdb migration-history
    """
    import subprocess

    setup_logging(verbose)

    console.print("📜 [bold cyan]Migration History[/bold cyan]\n")

    try:
        # Show current revision
        cmd_current = ["uv", "run", "alembic", "current"]
        result_current = subprocess.run(cmd_current, check=True, capture_output=True, text=True)

        console.print("[bold]Current Revision:[/bold]")
        if result_current.stdout:
            console.print(result_current.stdout)
        else:
            console.print("  No migrations applied yet\n")

        # Show history
        cmd_history = ["uv", "run", "alembic", "history", "--verbose"]
        result_history = subprocess.run(cmd_history, check=True, capture_output=True, text=True)

        console.print("\n[bold]Migration History:[/bold]")
        if result_history.stdout:
            console.print(result_history.stdout)

    except subprocess.CalledProcessError as e:
        console.print(f"\n❌ [bold red]Failed to get migration history![/bold red]")
        if e.stderr:
            console.print(f"Error: {e.stderr}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"\n❌ [bold red]Failed to get migration history: {e}[/bold red]")
        raise typer.Exit(code=1)


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()

