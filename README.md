# PDF Context Narrator

A Python 3.11 CLI tool for ingesting, searching, and analyzing PDF documents.

## Features

- 📥 **Ingest**: Process and index PDF documents
- 🔍 **Search**: Query indexed documents with powerful search
- 📄 **Summarize**: Generate summaries of PDF content
- 📅 **Timeline**: Create chronological views of document events
- 📤 **Export**: Export data in multiple formats (JSON, CSV, Markdown)

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

Or install as a package (recommended for development):
```bash
pip install -e .
```

## Usage

### Python API

```python
from src.pdf_text_extractor import PDFTextExtractor

# Initialize extractor
extractor = PDFTextExtractor(output_dir="data/extracted")

# Extract text from a PDF
output_path = extractor.process_pdf("path/to/your/document.pdf")

# Or extract specific pages
page_data = extractor.extract_page("path/to/document.pdf", page_num=0)
```

### Command Line

```bash
python example.py path/to/your/document.pdf
```

## Output Format

The extracted text is saved in JSONL (JSON Lines) format, with one JSON object per line:

```json
{"file": "/path/to/document.pdf", "page": 0, "chars": 1234, "extraction_method": "pypdf", "text": "Extracted text..."}
{"file": "/path/to/document.pdf", "page": 1, "chars": 987, "extraction_method": "pypdf", "text": "More text..."}
```

Each line contains:
- `file`: Absolute path to the source PDF
- `page`: Page number (0-indexed)
- `chars`: Number of characters extracted
- `extraction_method`: Either "pypdf" or "pdfplumber"
- `text`: The extracted text content

## Testing

Run the test suite:

```bash
python -m unittest tests.test_pdf_text_extractor -v
```

## How It Works

1. **Primary Extraction (pypdf)**: The tool first attempts to extract text using `pypdf`, which is fast and handles most PDFs well
2. **Fallback (pdfplumber)**: If `pypdf` fails (encrypted, corrupt, or no text extracted), it automatically falls back to `pdfplumber`
3. **Graceful Degradation**: If a page fails to extract with both methods, it logs a warning and continues processing remaining pages
4. **Metadata Collection**: Each successful extraction includes metadata about the source file, page number, text length, and method used

## Error Handling

The tool handles various PDF issues gracefully:

- **Encrypted PDFs**: Detected and logged, with fallback attempted
- **Corrupt Pages**: Individual page failures don't stop processing
- **Missing Dependencies**: Checks for required libraries and provides helpful warnings
- **File Not Found**: Clear error messages for missing files

## Project Structure

```
PDF-Scanner/
├── src/
│   ├── __init__.py
│   └── pdf_text_extractor.py    # Main extraction logic
├── tests/
│   ├── __init__.py
│   └── test_pdf_text_extractor.py  # Comprehensive unit tests
├── data/
│   └── extracted/                # Output directory for JSONL files
├── example.py                    # Example usage script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## License

See repository for license information.
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

⚠️ **Note**: This is currently a scaffolding implementation. All commands are stubs and do not perform actual PDF processing. Business logic will be implemented in future releases.

## Roadmap

- [ ] Implement PDF text extraction
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
