"""CLI interface for PDF Context Narrator using Typer."""

import typer
from typing import Optional
from pathlib import Path

from pdf_context_narrator.config import get_settings
from pdf_context_narrator.logger import get_logger

app = typer.Typer(
    name="pdf-context-narrator",
    help="A tool for ingesting, searching, and analyzing PDF documents.",
    add_completion=False,
)

logger = get_logger(__name__)


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Path to PDF file or directory to ingest"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Recursively ingest PDFs from subdirectories"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-ingestion of already processed files"
    ),
) -> None:
    """
    Ingest PDF documents into the system.

    This command processes PDF files and stores their content for later retrieval.
    """
    settings = get_settings()
    logger.info(f"Ingesting PDFs from: {path}")
    logger.info(f"Recursive: {recursive}, Force: {force}")
    logger.info(f"Using data directory: {settings.data_dir}")

    typer.echo(f"📥 Ingesting PDFs from: {path}")
    typer.echo("✅ Ingestion complete (stub implementation)")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results to return"),
    format: str = typer.Option("text", "--format", "-f", help="Output format (text, json)"),
) -> None:
    """
    Search through ingested PDF documents.

    This command searches the indexed content and returns relevant results.
    """
    get_settings()
    logger.info(f"Searching for: {query}")
    logger.info(f"Limit: {limit}, Format: {format}")

    typer.echo(f"🔍 Searching for: {query}")
    typer.echo(f"📊 Showing top {limit} results")
    typer.echo("✅ Search complete (stub implementation)")


@app.command()
def summarize(
    document: Path = typer.Argument(..., help="Path to document or document ID"),
    length: str = typer.Option(
        "medium", "--length", "-l", help="Summary length (short, medium, long)"
    ),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """
    Generate a summary of a PDF document.

    This command creates a concise summary of the document's content.
    """
    get_settings()
    logger.info(f"Summarizing document: {document}")
    logger.info(f"Summary length: {length}")

    typer.echo(f"📄 Summarizing document: {document}")
    typer.echo(f"📝 Summary length: {length}")
    if output:
        typer.echo(f"💾 Saving to: {output}")
    typer.echo("✅ Summary complete (stub implementation)")


@app.command()
def timeline(
    start_date: Optional[str] = typer.Option(None, "--start", "-s", help="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = typer.Option(None, "--end", "-e", help="End date (YYYY-MM-DD)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """
    Generate a timeline view of document events.

    This command creates a chronological view of document-related events.
    """
    get_settings()
    logger.info("Generating timeline")
    logger.info(f"Date range: {start_date} to {end_date}")

    typer.echo("📅 Generating timeline")
    if start_date:
        typer.echo(f"  Start: {start_date}")
    if end_date:
        typer.echo(f"  End: {end_date}")
    if output:
        typer.echo(f"💾 Saving to: {output}")
    typer.echo("✅ Timeline generation complete (stub implementation)")


@app.command()
def export(
    format: str = typer.Argument(..., help="Export format (json, csv, markdown)"),
    output: Path = typer.Argument(..., help="Output file path"),
    filter: Optional[str] = typer.Option(
        None, "--filter", help="Filter expression for documents to export"
    ),
) -> None:
    """
    Export data in various formats.

    This command exports the indexed data to different file formats.
    """
    get_settings()
    logger.info(f"Exporting data to {format} format")
    logger.info(f"Output path: {output}")

    typer.echo(f"📤 Exporting data to {format} format")
    typer.echo(f"💾 Output: {output}")
    if filter:
        typer.echo(f"🔍 Filter: {filter}")
    typer.echo("✅ Export complete (stub implementation)")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to configuration file"
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile (local, offline, cloud)"
    ),
    structured_logs: bool = typer.Option(
        False, "--structured-logs", help="Enable structured JSON logging"
    ),
) -> None:
    """
    PDF Context Narrator - A tool for ingesting, searching, and analyzing PDF documents.
    """
    from pdf_context_narrator.config import get_settings, clear_settings_cache
    from pdf_context_narrator.logger import setup_logging

    # Clear any cached settings to allow reloading with new config
    clear_settings_cache()

    # Load settings based on config or profile
    if config:
        settings = get_settings(config_path=config)
        logger.info(f"Using config file: {config}")
    elif profile:
        settings = get_settings(profile=profile)
        logger.info(f"Using profile: {profile}")
    else:
        settings = get_settings()

    # Setup logging with structured logging if requested
    log_level = "DEBUG" if verbose else settings.log_level
    use_structured = structured_logs or settings.structured_logging
    setup_logging(level=log_level, structured=use_structured)

    if verbose:
        logger.debug("Verbose mode enabled")
    if use_structured:
        logger.debug("Structured logging enabled")


if __name__ == "__main__":
    app()
