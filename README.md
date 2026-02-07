# PDF-Scanner

A robust PDF text extraction tool with intelligent fallback handling.

## Features

- **Dual Extraction Strategy**: Uses `pypdf` as the primary extraction method with automatic fallback to `pdfplumber` for better reliability
- **Per-Page Metadata**: Extracts text with detailed metadata including:
  - File path
  - Page number
  - Character count
  - Extraction method used
- **Graceful Error Handling**: 
  - Handles encrypted PDFs
  - Manages corrupt pages without stopping the entire process
  - Continues processing even when individual pages fail
- **JSONL Output**: Saves extracted text in JSONL format for easy processing and analysis
- **Comprehensive Testing**: Full unit test coverage for parser and fallback behavior

## Installation

1. Clone the repository:
```bash
git clone https://github.com/wesire/PDF-Scanner.git
cd PDF-Scanner
```

2. Install dependencies:
```bash
pip install -r requirements.txt
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