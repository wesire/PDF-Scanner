# PDF Context Narrator

A Python 3.11 CLI tool for ingesting, searching, and analyzing PDF documents with large-file resilience.

## Features

- 📥 **Ingest**: Process and index PDF documents with resilience features
  - **Streaming page processing** for memory efficiency
  - **Automatic checkpoints** every N pages (configurable)
  - **Resumable runs** to continue from interruption
  - **Multiprocessing support** for faster processing
  - **Progress bars** for visual feedback
  - **Memory limit monitoring** (optional, requires psutil)
- 🔍 **Search**: Query indexed documents with powerful search
- 📄 **Summarize**: Generate summaries of PDF content
- 📅 **Timeline**: Create chronological views of document events
- 📤 **Export**: Export data in multiple formats (JSON, CSV, Markdown)

## Large-File Resilience

The PDF processor is designed to handle large files (1000+ pages) without crashing:

- **Streaming Processing**: Pages are processed one at a time, not loading the entire PDF into memory
- **Checkpoints**: State is saved every N pages (configurable via `--batch-size`)
- **Resume Capability**: If processing is interrupted, use `--resume` to continue from the last checkpoint
- **Multiprocessing**: Use `--workers` to process pages in parallel (where applicable)
- **Progress Tracking**: Visual progress bars show processing status
- **Memory Monitoring**: Optional memory limit to prevent out-of-memory errors

## Project Structure

```
pdf_context_narrator/
├── src/
│   └── pdf_context_narrator/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py          # CLI interface with Typer
│       ├── config.py       # Configuration management with Pydantic
│       └── logger.py       # Logging setup
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
- `PDF_CN_BATCH_SIZE`: Number of pages between checkpoints (default: `10`)
- `PDF_CN_CHECKPOINT_DIR`: Directory for checkpoint files (default: `checkpoints`)
- `PDF_CN_MEMORY_LIMIT_MB`: Optional memory limit in MB (requires psutil)

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

Process and index PDF documents with large-file resilience:

```bash
# Ingest a single PDF file
python -m pdf_context_narrator ingest path/to/document.pdf

# Ingest all PDFs in a directory
python -m pdf_context_narrator ingest path/to/pdfs/

# Recursively ingest PDFs from subdirectories
python -m pdf_context_narrator ingest path/to/pdfs/ --recursive

# Force re-ingestion of already processed files
python -m pdf_context_narrator ingest path/to/pdfs/ --force

# Use multiple workers for parallel processing
python -m pdf_context_narrator ingest path/to/pdfs/ --workers 8

# Set checkpoint frequency (pages between checkpoints)
python -m pdf_context_narrator ingest path/to/pdfs/ --batch-size 50

# Resume from checkpoint after interruption
python -m pdf_context_narrator ingest path/to/pdfs/ --resume

# Set memory limit (requires psutil)
python -m pdf_context_narrator ingest path/to/pdfs/ --memory-limit 1024

# Custom checkpoint directory
python -m pdf_context_narrator ingest path/to/pdfs/ --checkpoint-dir ./my_checkpoints
```

**Large File Processing:**

When processing large PDFs (1000+ pages):
1. Processing is done via streaming, one page at a time
2. Checkpoints are automatically saved every N pages (default: 10)
3. If interrupted (Ctrl+C), the checkpoint is saved
4. Use `--resume` to continue from the last checkpoint
5. Progress bars show real-time processing status

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

### Example 1: Process Large PDF with Resilience

```bash
# Process a large PDF with checkpoints every 100 pages
python -m pdf_context_narrator ingest large_document.pdf --batch-size 100

# If interrupted (Ctrl+C), resume from checkpoint
python -m pdf_context_narrator ingest large_document.pdf --resume --batch-size 100

# Use multiple workers for faster processing
python -m pdf_context_narrator ingest large_document.pdf --workers 8 --batch-size 100
```

### Example 2: Process and Search PDFs

```bash
# 1. Ingest PDFs from a directory
python -m pdf_context_narrator ingest ./documents/ --recursive

# 2. Search for specific content
python -m pdf_context_narrator search "machine learning" --limit 5

# 3. Export results
python -m pdf_context_narrator export json results.json
```

### Example 3: Summarize Multiple Documents

```bash
# Process PDFs and generate summaries
python -m pdf_context_narrator ingest ./reports/
python -m pdf_context_narrator summarize ./reports/report1.pdf --output summary1.txt
python -m pdf_context_narrator summarize ./reports/report2.pdf --output summary2.txt
```

### Example 4: Timeline Analysis

```bash
# Ingest documents with date metadata
python -m pdf_context_narrator ingest ./historical-docs/ --recursive

# Generate timeline for specific period
python -m pdf_context_narrator timeline --start 2023-01-01 --end 2023-12-31 --output timeline.json
```

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

## Development

## Current Status

✅ **PDF Ingestion**: Full implementation with large-file resilience
  - Streaming page processing
  - Automatic checkpoints and resume capability
  - Multiprocessing support
  - Progress bars and memory monitoring

⚠️ **Other Commands**: Stub implementations - business logic to be implemented in future releases.

## Roadmap

- [x] Implement PDF text extraction with streaming
- [x] Add checkpoint/resume capability for large files
- [x] Add progress bars and status feedback
- [x] Implement multiprocessing support
- [ ] Add vector database for semantic search
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