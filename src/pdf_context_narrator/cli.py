"""CLI interface for PDF Context Narrator using Typer."""

import typer
from typing import Optional
from pathlib import Path

from pdf_context_narrator.config import get_settings
from pdf_context_narrator.logger import get_logger
from pdf_context_narrator.processor import process_pdf_file

app = typer.Typer(
    name="pdf-context-narrator",
    help="A tool for ingesting, searching, and analyzing PDF documents.",
    add_completion=False,
)

logger = get_logger(__name__)


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Path to PDF file or directory to ingest"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recursively ingest PDFs from subdirectories"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-ingestion of already processed files"),
    workers: Optional[int] = typer.Option(None, "--workers", "-w", help="Number of parallel workers for multiprocessing"),
    batch_size: Optional[int] = typer.Option(None, "--batch-size", "-b", help="Number of pages between checkpoints"),
    memory_limit: Optional[int] = typer.Option(None, "--memory-limit", "-m", help="Memory limit in MB (requires psutil)"),
    resume: bool = typer.Option(False, "--resume", help="Resume from checkpoint if available"),
    checkpoint_dir: Optional[Path] = typer.Option(None, "--checkpoint-dir", help="Directory for checkpoint files"),
) -> None:
    """
    Ingest PDF documents into the system with large-file resilience.
    
    This command processes PDF files with streaming page processing, automatic
    checkpoints, resumable runs, and optional multiprocessing support.
    
    Features:
    - Streaming page processing for memory efficiency
    - Automatic checkpoints every N pages (configurable via --batch-size)
    - Resume capability with --resume flag
    - Multiprocessing support with --workers flag
    - Progress bars for visual feedback
    - Memory limit monitoring with --memory-limit flag
    """
    settings = get_settings()
    
    # Use settings defaults if not specified
    workers_count = workers if workers is not None else settings.max_workers
    batch_size_val = batch_size if batch_size is not None else settings.batch_size
    checkpoint_dir_val = checkpoint_dir if checkpoint_dir is not None else settings.checkpoint_dir
    
    logger.info(f"Ingesting PDFs from: {path}")
    logger.info(f"Configuration: recursive={recursive}, force={force}, resume={resume}")
    logger.info(f"Workers: {workers_count}, Batch size: {batch_size_val}")
    
    typer.echo(f"📥 Ingesting PDFs from: {path}")
    typer.echo(f"⚙️  Workers: {workers_count}, Batch size: {batch_size_val}")
    
    if resume:
        typer.echo(f"🔄 Resume mode enabled, checkpoint dir: {checkpoint_dir_val}")
    
    # Process single file or directory
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            typer.echo(f"❌ Error: Not a PDF file: {path}", err=True)
            raise typer.Exit(1)
        
        try:
            result = process_pdf_file(
                pdf_path=path,
                workers=workers_count,
                batch_size=batch_size_val,
                memory_limit_mb=memory_limit,
                checkpoint_dir=checkpoint_dir_val,
                resume=resume,
                force=force,
            )
            
            if result["completed"]:
                typer.echo(
                    f"✅ Successfully processed {result['processed_pages']}/{result['total_pages']} pages"
                )
            else:
                typer.echo(
                    f"⚠️  Processing interrupted at page {result['processed_pages']}/{result['total_pages']}"
                )
                typer.echo(f"💾 Checkpoint saved. Run with --resume to continue.")
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")
            typer.echo(f"❌ Error: {e}", err=True)
            raise typer.Exit(1)
    
    elif path.is_dir():
        # Process directory
        pdf_files = []
        if recursive:
            pdf_files = list(path.rglob("*.pdf"))
        else:
            pdf_files = list(path.glob("*.pdf"))
        
        if not pdf_files:
            typer.echo(f"⚠️  No PDF files found in {path}")
            return
        
        typer.echo(f"📚 Found {len(pdf_files)} PDF file(s)")
        
        success_count = 0
        error_count = 0
        interrupted_count = 0
        
        for pdf_file in pdf_files:
            typer.echo(f"\n📄 Processing: {pdf_file.name}")
            try:
                result = process_pdf_file(
                    pdf_path=pdf_file,
                    workers=workers_count,
                    batch_size=batch_size_val,
                    memory_limit_mb=memory_limit,
                    checkpoint_dir=checkpoint_dir_val,
                    resume=resume,
                    force=force,
                )
                
                if result["completed"]:
                    success_count += 1
                    typer.echo(f"   ✅ {result['processed_pages']} pages processed")
                else:
                    interrupted_count += 1
                    typer.echo(f"   ⚠️  Interrupted at page {result['processed_pages']}")
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing {pdf_file}: {e}")
                typer.echo(f"   ❌ Error: {e}")
        
        typer.echo(f"\n📊 Summary:")
        typer.echo(f"   ✅ Successful: {success_count}")
        typer.echo(f"   ⚠️  Interrupted: {interrupted_count}")
        typer.echo(f"   ❌ Errors: {error_count}")
    else:
        typer.echo(f"❌ Error: Path not found: {path}", err=True)
        raise typer.Exit(1)


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
    settings = get_settings()
    logger.info(f"Searching for: {query}")
    logger.info(f"Limit: {limit}, Format: {format}")
    
    typer.echo(f"🔍 Searching for: {query}")
    typer.echo(f"📊 Showing top {limit} results")
    typer.echo("✅ Search complete (stub implementation)")


@app.command()
def summarize(
    document: Path = typer.Argument(..., help="Path to document or document ID"),
    length: str = typer.Option("medium", "--length", "-l", help="Summary length (short, medium, long)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """
    Generate a summary of a PDF document.
    
    This command creates a concise summary of the document's content.
    """
    settings = get_settings()
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
    settings = get_settings()
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
    filter: Optional[str] = typer.Option(None, "--filter", help="Filter expression for documents to export"),
) -> None:
    """
    Export data in various formats.
    
    This command exports the indexed data to different file formats.
    """
    settings = get_settings()
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
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to configuration file"),
) -> None:
    """
    PDF Context Narrator - A tool for ingesting, searching, and analyzing PDF documents.
    """
    if verbose:
        logger.setLevel("DEBUG")
        logger.debug("Verbose mode enabled")
    
    if config:
        logger.info(f"Using config file: {config}")


if __name__ == "__main__":
    app()
