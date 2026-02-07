# Text Extraction and Normalization Modules

This document describes the refactored text extraction and normalization functionality.

## Overview

The PDF text extraction logic has been refactored into two separate modules:

1. **`extract.py`** - Core text extraction from PDF files
2. **`normalize.py`** - Text normalization and OCR error correction

## Modules

### extract.py

Provides functions for extracting text from PDF files using multiple extraction methods:

- `extract_text_pypdf(pdf_path, page_num)` - Extract using pypdf library
- `extract_text_pdfplumber(pdf_path, page_num)` - Extract using pdfplumber (fallback)
- `extract_text(pdf_path, page_num)` - Main function with automatic fallback

**Key Features:**
- Automatic fallback from pypdf to pdfplumber
- Handles encrypted PDFs gracefully
- Returns extraction method used
- Comprehensive error handling

### normalize.py

Provides functions for normalizing OCR-extracted text:

- `normalize_text(text)` - Main normalization function
- `preserve_part_numbers(text)` - Extract part numbers from text
- `validate_part_number(part_number)` - Validate part number format

**Key Features:**

1. **Preserves Part Numbers**: Maintains part numbers in the format `#K-####-#`
   - Example: `#K-1234-5`, `#K-9876-3`
   
2. **Fixes OCR Ligature Issues**:
   - `ﬁ` → `fi` (fi ligature)
   - `ﬂ` → `fl` (fl ligature)
   - `ﬀ` → `ff` (ff ligature)
   - `ﬃ` → `ffi` (ffi ligature)
   - `ﬄ` → `ffl` (ffl ligature)
   - `ﬅ`, `ﬆ` → `st` (st ligatures)

3. **Fixes OCR Apostrophe Issues**:
   - `'`, `'` → `'` (right/left single quotes)
   - `‛` → `'` (reversed quotation mark)
   - `′` → `'` (prime)
   - `` ` `` → `'` (grave accent)
   - `´` → `'` (acute accent)

4. **Preserves Line-Item Boundaries**:
   - Maintains line breaks between items
   - Reduces excessive blank lines to double newline
   - Normalizes line endings to `\n`

5. **Whitespace Normalization**:
   - Converts multiple spaces to single space
   - Removes leading/trailing whitespace
   - Handles tabs consistently

## Usage Examples

### Basic Text Extraction

```python
from extract import extract_text

# Extract text from a PDF page
text, method = extract_text("document.pdf", page_num=0)
print(f"Extracted using {method}: {text}")
```

### Text Normalization

```python
from normalize import normalize_text, preserve_part_numbers

# OCR text with errors
ocr_text = """Part #K-1234-5 - High-efﬁciency pump
The manufacturer's warranty covers ﬁnancial losses."""

# Normalize the text
normalized = normalize_text(ocr_text)
print(normalized)
# Output:
# Part #K-1234-5 - High-efficiency pump
# The manufacturer's warranty covers financial losses.

# Extract part numbers
parts = preserve_part_numbers(normalized)
print(parts)  # ['#K-1234-5']
```

### Integration with PDFTextExtractor

```python
from pdf_text_extractor import PDFTextExtractor

# Create extractor
extractor = PDFTextExtractor()

# Extract with normalization
page_data = extractor.extract_page("document.pdf", 0, normalize=True)
print(page_data['text'])  # Normalized text
```

## Testing

### Running Tests

```bash
# Run extract module tests
python -m unittest tests.test_extract

# Run normalize module tests  
python -m unittest tests.test_normalize

# Run all related tests
python -m unittest tests.test_extract tests.test_normalize tests.test_pdf_text_extractor
```

### Demo Script

A demonstration script is provided to show the normalization capabilities:

```bash
python demo_normalize.py
```

## Test Coverage

- **test_extract.py**: 11 tests covering all extraction scenarios
- **test_normalize.py**: 18 tests covering normalization features
- **Fixture data**: `tests/fixtures/parts_invoice.txt` with sample OCR text

## Backward Compatibility

The `PDFTextExtractor` class maintains full backward compatibility:
- All existing methods work unchanged
- New `normalize` parameter is optional (defaults to `False`)
- Gracefully handles missing refactored modules

## Part Number Format

The part number pattern is: `#K-####-#`

Where:
- `#` is the literal hash symbol
- `K` is the literal letter K
- `-` are literal hyphens
- `####` are exactly 4 digits (0-9)
- `#` is exactly 1 digit (0-9)

**Valid Examples:**
- `#K-1234-5`
- `#K-0000-0`
- `#K-9999-9`

**Invalid Examples:**
- `#K-123-5` (only 3 digits)
- `#K-12345-6` (5 digits)
- `K-1234-5` (missing #)
- `#A-1234-5` (wrong letter)

## Architecture

```
src/
├── extract.py          # Text extraction functions
├── normalize.py        # Text normalization functions
└── pdf_text_extractor.py  # High-level PDF processing (uses extract/normalize)

tests/
├── test_extract.py     # Tests for extraction
├── test_normalize.py   # Tests for normalization
└── fixtures/
    └── parts_invoice.txt  # Sample data with OCR issues
```

## Future Enhancements

Potential improvements:
- Support for additional part number formats
- More OCR error patterns
- Configurable normalization options
- Language-specific normalization rules
