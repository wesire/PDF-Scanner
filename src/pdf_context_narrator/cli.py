"""CLI interface for PDF Context Narrator using Typer."""

import typer
import json
from typing import Optional
from pathlib import Path

from pdf_context_narrator.config import get_settings
from pdf_context_narrator.logger import get_logger
from pdf_context_narrator.chunking import SemanticChunker, SourceReference
from pdf_context_narrator.embeddings import get_embeddings_provider
from pdf_context_narrator.index import FAISSIndexManager

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
