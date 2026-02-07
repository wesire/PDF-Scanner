"""CLI interface for PDF Context Narrator using Typer."""

import typer
import json
from typing import Optional
from pathlib import Path

from pdf_context_narrator.config import get_settings
from pdf_context_narrator.logger import get_logger
from pdf_context_narrator.processor import process_pdf_file
from pdf_context_narrator.search import SearchEngine
from pdf_context_narrator.chunking import SemanticChunker, SourceReference
from pdf_context_narrator.embeddings import get_embeddings_provider
from pdf_context_narrator.index import FAISSIndexManager
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
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Recursively ingest PDFs from subdirectories"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-ingestion of already processed files"
    ),
) -> None:
    """
    Ingest PDF documents into the system.

    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recursively ingest PDFs from subdirectories"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-ingestion of already processed files"),
    workers: Optional[int] = typer.Option(None, "--workers", "-w", help="Number of parallel workers for multiprocessing"),
    batch_size: Optional[int] = typer.Option(None, "--batch-size", "-b", help="Number of pages between checkpoints"),
    memory_limit: Optional[int] = typer.Option(None, "--memory-limit", "-m", help="Memory limit in MB (requires psutil)"),
    resume: bool = typer.Option(False, "--resume", help="Resume from checkpoint if available"),
    checkpoint_dir: Optional[Path] = typer.Option(None, "--checkpoint-dir", help="Directory for checkpoint files"),
    ocr_mode: OCRMode = typer.Option(OCRMode.AUTO, "--ocr-mode", help="OCR processing mode: off (no OCR), auto (OCR low-text pages), force (OCR all pages)"),
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
    This command processes PDF files and stores their content for later retrieval.
    Supports OCR for scanned documents and images.
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

    This command searches the indexed content and returns relevant results.
    
    This command searches the indexed content and returns relevant results
    using hybrid keyword + vector ranking.
    """
    get_settings()
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


@app.command()
def rebuild_index(
    jsonl_path: Path = typer.Argument(..., help="Path to extracted JSONL file"),
    index_path: Optional[Path] = typer.Option(None, "--index-path", "-i", help="Path to save index"),
    model: str = typer.Option("all-MiniLM-L6-v2", "--model", "-m", help="Sentence transformer model name"),
) -> None:
    """
    Rebuild the vector index from extracted JSONL data.
    
    This command reads text data from a JSONL file, chunks it, generates embeddings,
    and builds a FAISS index for semantic search.
    """
    settings = get_settings()
    
    if not jsonl_path.exists():
        typer.echo(f"❌ Error: JSONL file not found: {jsonl_path}", err=True)
        raise typer.Exit(1)
    
    # Determine index path
    if index_path is None:
        index_path = settings.data_dir / "index"
    
    typer.echo(f"🔨 Rebuilding index from: {jsonl_path}")
    logger.info(f"Reading JSONL file: {jsonl_path}")
    
    try:
        # Read JSONL file
        documents = []
        with open(jsonl_path, "r") as f:
            for line in f:
                if line.strip():
                    documents.append(json.loads(line))
        
        typer.echo(f"📄 Loaded {len(documents)} documents")
        logger.info(f"Loaded {len(documents)} documents from JSONL")
        
        # Initialize chunker
        typer.echo("✂️  Chunking documents...")
        chunker = SemanticChunker(
            min_chunk_size=800,
            max_chunk_size=1200,
            overlap_size=120,
        )
        
        # Chunk all documents
        all_chunks = []
        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue
            
            source = SourceReference(
                file=doc.get("file", "unknown"),
                page=doc.get("page"),
                section=doc.get("section"),
            )
            
            chunks = chunker.chunk_text(text, source, metadata=doc.get("metadata", {}))
            all_chunks.extend(chunks)
        
        typer.echo(f"✅ Created {len(all_chunks)} chunks")
        logger.info(f"Created {len(all_chunks)} chunks")
        
        # Initialize embeddings provider
        typer.echo(f"🔧 Loading embeddings model: {model}")
        embeddings = get_embeddings_provider(
            provider="sentence-transformer",
            model_name=model,
            cache_dir=settings.cache_dir,
        )
        
        # Initialize index manager
        typer.echo("🗄️  Building FAISS index...")
        index_manager = FAISSIndexManager(
            embeddings_provider=embeddings,
            index_path=index_path,
        )
        
        # Rebuild index
        index_manager.rebuild(all_chunks)
        
        # Save index
        index_manager.save()
        typer.echo(f"💾 Index saved to: {index_path}")
        
        # Display stats
        stats = index_manager.get_stats()
        typer.echo("\n📊 Index Statistics:")
        typer.echo(f"  Total vectors: {stats['total_vectors']}")
        typer.echo(f"  Dimension: {stats['dimension']}")
        typer.echo(f"  Metadata count: {stats['metadata_count']}")
        
        typer.echo("\n✅ Index rebuild complete!")
        
    except Exception as e:
        typer.echo(f"❌ Error rebuilding index: {str(e)}", err=True)
        logger.error(f"Error rebuilding index: {str(e)}", exc_info=True)
        raise typer.Exit(1)


@app.command()
def index_info(
    index_path: Optional[Path] = typer.Option(None, "--index-path", "-i", help="Path to index"),
) -> None:
    """
    Display information about the vector index.
    """
    settings = get_settings()
    
    # Determine index path
    if index_path is None:
        index_path = settings.data_dir / "index"
    
    index_file = index_path.with_suffix(".faiss")
    metadata_file = index_path.with_suffix(".meta.json")
    
    if not index_file.exists():
        typer.echo(f"❌ Index not found: {index_file}", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"📊 Index Information: {index_path}")
    
    try:
        # Load and display index stats
        embeddings = get_embeddings_provider(
            provider="sentence-transformer",
            model_name="all-MiniLM-L6-v2",
        )
        index_manager = FAISSIndexManager(
            embeddings_provider=embeddings,
            index_path=index_path,
        )
        index_manager.load()
        
        stats = index_manager.get_stats()
        typer.echo(f"\n  Total vectors: {stats['total_vectors']}")
        typer.echo(f"  Dimension: {stats['dimension']}")
        typer.echo(f"  Metadata entries: {stats['metadata_count']}")
        typer.echo(f"\n  Index file: {index_file}")
        typer.echo(f"  Index size: {index_file.stat().st_size / 1024:.2f} KB")
        typer.echo(f"  Metadata file: {metadata_file}")
        typer.echo(f"  Metadata size: {metadata_file.stat().st_size / 1024:.2f} KB")
        
    except Exception as e:
        typer.echo(f"❌ Error loading index: {str(e)}", err=True)
        logger.error(f"Error loading index: {str(e)}", exc_info=True)
        raise typer.Exit(1)


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
