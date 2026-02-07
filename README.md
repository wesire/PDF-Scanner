# PDF Context Narrator

A Python 3.11 CLI tool for ingesting, searching, and analyzing PDF documents with semantic search capabilities.

## Features

- 📥 **Ingest**: Process and index PDF documents
- 🔍 **Search**: Query indexed documents with powerful semantic search
- 📄 **Summarize**: Generate summaries of PDF content
- 📅 **Timeline**: Create chronological views of document events
- 📤 **Export**: Export data in multiple formats (JSON, CSV, Markdown)
- 🧩 **Chunking**: Semantic text chunking with configurable size and overlap
- 🔢 **Embeddings**: Text embeddings using Sentence Transformers
- 🗄️ **Vector Index**: FAISS-based vector index for efficient similarity search

## Project Structure

```
pdf_context_narrator/
├── src/
│   └── pdf_context_narrator/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py          # CLI interface with Typer
│       ├── config.py       # Configuration management with Pydantic
│       ├── logger.py       # Logging setup
│       ├── chunking.py     # Semantic text chunking
│       ├── embeddings.py   # Embeddings abstraction
│       └── index.py        # FAISS index manager
├── tests/                   # Test files
├── configs/                 # Configuration files
├── docs/                    # Documentation
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/wesire/PDF-Scanner.git
cd PDF-Scanner
```

2. Create and activate a virtual environment (recommended):
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your preferred settings
```

## Configuration

The application uses environment variables for configuration. All settings are prefixed with `PDF_CN_`.

Key configuration options:
- `PDF_CN_DATA_DIR`: Directory for storing data (default: `data`)
- `PDF_CN_CACHE_DIR`: Directory for cache files (default: `cache`)
- `PDF_CN_LOGS_DIR`: Directory for log files (default: `logs`)
- `PDF_CN_LOG_LEVEL`: Logging level (default: `INFO`)
- `PDF_CN_MAX_WORKERS`: Number of parallel workers (default: `4`)

See `.env.example` for all available options.

## Usage

The application provides a command-line interface with several commands:

### Running the Application

You can run the application in several ways:

```bash
# Method 1: As a module
python -m pdf_context_narrator [COMMAND] [OPTIONS]

# Method 2: Direct execution
python src/pdf_context_narrator/cli.py [COMMAND] [OPTIONS]
```

### Available Commands

#### 1. Ingest PDFs

Process and index PDF documents:

```bash
# Ingest a single PDF file
python -m pdf_context_narrator ingest path/to/document.pdf

# Ingest all PDFs in a directory
python -m pdf_context_narrator ingest path/to/pdfs/

# Recursively ingest PDFs from subdirectories
python -m pdf_context_narrator ingest path/to/pdfs/ --recursive

# Force re-ingestion of already processed files
python -m pdf_context_narrator ingest path/to/pdfs/ --force
```

#### 2. Search Documents

Search through indexed documents:

```bash
# Basic search
python -m pdf_context_narrator search "your search query"

# Limit number of results
python -m pdf_context_narrator search "your query" --limit 20

# Output as JSON
python -m pdf_context_narrator search "your query" --format json
```

#### 3. Summarize Documents

Generate document summaries:

```bash
# Summarize a document
python -m pdf_context_narrator summarize path/to/document.pdf

# Create a longer summary
python -m pdf_context_narrator summarize path/to/document.pdf --length long

# Save summary to file
python -m pdf_context_narrator summarize path/to/document.pdf --output summary.txt
```

#### 4. Generate Timeline

Create chronological views:

```bash
# Generate timeline for all documents
python -m pdf_context_narrator timeline

# Filter by date range
python -m pdf_context_narrator timeline --start 2024-01-01 --end 2024-12-31

# Save timeline to file
python -m pdf_context_narrator timeline --output timeline.json
```

#### 5. Export Data

Export indexed data in various formats:

```bash
# Export to JSON
python -m pdf_context_narrator export json output.json

# Export to CSV
python -m pdf_context_narrator export csv output.csv

# Export to Markdown
python -m pdf_context_narrator export markdown output.md

# Export with filter
python -m pdf_context_narrator export json output.json --filter "status:processed"
```

#### 6. Rebuild Index

Build or rebuild the vector index from extracted JSONL data:

```bash
# Rebuild index from JSONL file
python -m pdf_context_narrator rebuild-index extracted_data.jsonl

# Specify custom index path
python -m pdf_context_narrator rebuild-index extracted_data.jsonl --index-path /path/to/index

# Use different embedding model
python -m pdf_context_narrator rebuild-index extracted_data.jsonl --model all-mpnet-base-v2
```

The JSONL file should contain one JSON object per line with the following structure:
```json
{
  "file": "document.pdf",
  "page": 1,
  "section": "Introduction",
  "text": "Document text content...",
  "metadata": {"author": "Author Name", "date": "2024-01-01"}
}
```

#### 7. Index Information

Display information about the vector index:

```bash
# Show index statistics
python -m pdf_context_narrator index-info

# Check specific index
python -m pdf_context_narrator index-info --index-path /path/to/index
```

### Global Options

All commands support these global options:

```bash
# Enable verbose output
python -m pdf_context_narrator --verbose [COMMAND]

# Use custom config file
python -m pdf_context_narrator --config path/to/config.yaml [COMMAND]

# Show help
python -m pdf_context_narrator --help

# Show help for a specific command
python -m pdf_context_narrator [COMMAND] --help
```

## Examples

Here are some complete workflow examples:

### Example 1: Process and Search PDFs

```bash
# 1. Ingest PDFs from a directory
python -m pdf_context_narrator ingest ./documents/ --recursive

# 2. Search for specific content
python -m pdf_context_narrator search "machine learning" --limit 5

# 3. Export results
python -m pdf_context_narrator export json results.json
```

### Example 2: Summarize Multiple Documents

```bash
# Process PDFs and generate summaries
python -m pdf_context_narrator ingest ./reports/
python -m pdf_context_narrator summarize ./reports/report1.pdf --output summary1.txt
python -m pdf_context_narrator summarize ./reports/report2.pdf --output summary2.txt
```

### Example 3: Timeline Analysis

```bash
# Ingest documents with date metadata
python -m pdf_context_narrator ingest ./historical-docs/ --recursive

# Generate timeline for specific period
python -m pdf_context_narrator timeline --start 2023-01-01 --end 2023-12-31 --output timeline.json
```

### Example 4: Building Semantic Search Index

```bash
# Create sample JSONL from your extracted data
# (This would typically be generated by a PDF extraction process)

# Rebuild vector index from JSONL
python -m pdf_context_narrator rebuild-index extracted_documents.jsonl

# Check index statistics
python -m pdf_context_narrator index-info

# The index can now be used for semantic search
python -m pdf_context_narrator search "machine learning applications"
```

## Architecture

### Text Chunking

The system uses semantic chunking to split documents into manageable pieces:

- **Target chunk size**: 800-1200 characters
- **Overlap**: 120 characters between consecutive chunks
- **Smart boundaries**: Respects paragraph, sentence, and word boundaries
- **Metadata preservation**: Each chunk maintains references to source file, page, and section

### Embeddings

Text embeddings are generated using Sentence Transformers:

- **Default model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Abstraction layer**: Easy to swap models or providers
- **Batch processing**: Efficient embedding generation for multiple texts
- **Caching**: Models are cached locally for performance

### Vector Index

FAISS (Facebook AI Similarity Search) is used for efficient similarity search:

- **Index type**: Flat L2 (exact search)
- **Metadata storage**: JSON file alongside the index
- **Operations**: Save, load, update, and rebuild
- **Scalable**: Can handle millions of vectors efficiently

## Development

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=pdf_context_narrator tests/
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## Current Status

✅ **Implemented Features**:
- Semantic text chunking with configurable size and overlap
- Embeddings abstraction with Sentence Transformers support
- FAISS vector index with save/load/update operations
- CLI commands for rebuilding index and viewing index information
- Comprehensive test suite for chunking, embeddings, and indexing

⚠️ **Note**: PDF extraction, summarization, and timeline features are stubs. These will be implemented in future releases.

## Roadmap

- [x] Add semantic text chunking
- [x] Add vector database (FAISS) for semantic search
- [x] Implement embeddings abstraction
- [ ] Implement PDF text extraction
- [ ] Integrate chunking with PDF ingestion
- [ ] Implement semantic search using the vector index
- [ ] Implement summarization using LLMs
- [ ] Add support for document metadata extraction
- [ ] Create web UI
- [ ] Add support for multiple document formats

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/wesire/PDF-Scanner).