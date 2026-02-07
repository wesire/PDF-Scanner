"""CLI interface for PDF Context Narrator using Typer."""

import typer
from typing import Optional
from pathlib import Path

from pdf_context_narrator.config import get_settings
from pdf_context_narrator.logger import get_logger
from pdf_context_narrator.search import SearchEngine
from pdf_context_narrator.ocr import OCRMode, PDFOCRProcessor

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
    ocr_mode: OCRMode = typer.Option(OCRMode.AUTO, "--ocr-mode", help="OCR processing mode: off (no OCR), auto (OCR low-text pages), force (OCR all pages)"),
) -> None:
    """
    Ingest PDF documents into the system.
    
    This command processes PDF files and stores their content for later retrieval.
    Supports OCR for scanned documents and images.
    """
    settings = get_settings()
    logger.info(f"Ingesting PDFs from: {path}")
    logger.info(f"Recursive: {recursive}, Force: {force}, OCR mode: {ocr_mode}")
    logger.info(f"Using data directory: {settings.data_dir}")
    
    typer.echo(f"📥 Ingesting PDFs from: {path}")
    typer.echo(f"🔍 OCR mode: {ocr_mode.value}")
    
    # Process based on whether path is a file or directory
    pdf_files = []
    if path.is_file():
        if path.suffix.lower() == '.pdf':
            pdf_files = [path]
        else:
            typer.echo(f"❌ Error: {path} is not a PDF file", err=True)
            raise typer.Exit(code=1)
    elif path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = list(path.glob(pattern))
        if not pdf_files:
            typer.echo(f"⚠️  No PDF files found in {path}", err=True)
            raise typer.Exit(code=1)
    else:
        typer.echo(f"❌ Error: {path} does not exist", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"📄 Found {len(pdf_files)} PDF file(s) to process")
    
    # Process each PDF with OCR
    try:
        processor = PDFOCRProcessor(ocr_mode=ocr_mode)
        
        for pdf_file in pdf_files:
            typer.echo(f"\n📖 Processing: {pdf_file.name}")
            try:
                pages = processor.process_pdf(pdf_file)
                
                # Display summary
                ocr_count = sum(1 for p in pages if p.ocr_applied)
                total_chars = sum(len(p.text) for p in pages)
                
                typer.echo(f"  ✅ Processed {len(pages)} page(s)")
                if ocr_count > 0:
                    typer.echo(f"  🔍 OCR applied to {ocr_count} page(s)")
                typer.echo(f"  📝 Extracted {total_chars} characters")
                
                # Log page details
                for page in pages:
                    logger.info(
                        f"Page {page.page_number}: "
                        f"chars={len(page.text)}, "
                        f"blocks={len(page.blocks)}, "
                        f"source={page.source}, "
                        f"ocr={page.ocr_applied}"
                    )
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                typer.echo(f"  ❌ Error: {e}", err=True)
                continue
        
        typer.echo(f"\n✅ Ingestion complete")
        
    except RuntimeError as e:
        logger.error(f"Failed to initialize OCR processor: {e}")
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results to return"),
    format: str = typer.Option("text", "--format", "-f", help="Output format (text, json, markdown)"),
    data_dir: Optional[Path] = typer.Option(None, "--data-dir", "-d", help="Directory containing documents to search"),
    keyword_weight: float = typer.Option(0.6, "--keyword-weight", help="Weight for keyword scoring (0-1)"),
    vector_weight: float = typer.Option(0.4, "--vector-weight", help="Weight for vector scoring (0-1)"),
    seed: int = typer.Option(42, "--seed", help="Random seed for deterministic results"),
) -> None:
    """
    Search through ingested PDF documents.
    
    This command searches the indexed content and returns relevant results
    using hybrid keyword + vector ranking.
    """
    settings = get_settings()
    logger.info(f"Searching for: {query}")
    logger.info(f"Limit: {limit}, Format: {format}")
    
    # Determine data directory
    search_dir = data_dir if data_dir else settings.data_dir
    
    # Initialize search engine
    engine = SearchEngine(seed=seed)
    
    # Index documents from data directory
    if search_dir.exists():
        typer.echo(f"📂 Indexing documents from: {search_dir}")
        engine.index_directory(search_dir, pattern="*.txt")
        
        if not engine.chunks:
            typer.echo("⚠️  No documents found to search. Please ingest documents first.")
            return
    else:
        typer.echo(f"⚠️  Data directory not found: {search_dir}")
        typer.echo("Please ingest documents first or specify a valid --data-dir")
        return
    
    # Perform search
    typer.echo(f"🔍 Searching for: {query}")
    results = engine.search(
        query=query,
        top_k=limit,
        keyword_weight=keyword_weight,
        vector_weight=vector_weight
    )
    
    if not results:
        typer.echo("No results found.")
        return
    
    # Output results
    if format == "json":
        output = engine.export_results_json(results)
        typer.echo(output)
    elif format == "markdown":
        output = engine.export_results_markdown(results, query)
        typer.echo(output)
    else:  # text format
        typer.echo(f"\n📊 Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            typer.echo(f"[{i}] {Path(result.document).name} (Page {result.page})")
            typer.echo(f"    Score: {result.score:.4f} (keyword: {result.keyword_score:.4f}, vector: {result.vector_score:.4f})")
            typer.echo(f"    Snippet: {result.snippet}")
            typer.echo()


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
