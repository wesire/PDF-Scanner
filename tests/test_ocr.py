"""Tests for OCR functionality."""

import pytest
from pathlib import Path
import tempfile

from pdf_context_narrator.ocr import (
    OCRMode,
    PDFOCRProcessor,
    PageText,
    TextBlock,
)

# Try to import reportlab for creating test PDFs
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_text_pdf(temp_dir):
    """Create a simple PDF with text for testing."""
    if not REPORTLAB_AVAILABLE:
        pytest.skip("reportlab not available for creating test PDFs")
    
    pdf_path = temp_dir / "simple_text.pdf"
    
    # Create a PDF with text
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "This is a test PDF document.")
    c.drawString(100, 730, "It contains multiple lines of text.")
    c.drawString(100, 710, "This should be extracted without OCR.")
    c.showPage()
    c.save()
    
    return pdf_path


@pytest.fixture
def low_text_pdf(temp_dir):
    """Create a PDF with minimal text (simulating a scanned page)."""
    if not REPORTLAB_AVAILABLE:
        pytest.skip("reportlab not available for creating test PDFs")
    
    pdf_path = temp_dir / "low_text.pdf"
    
    # Create a PDF with very little text
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "A")  # Just one character
    c.showPage()
    c.save()
    
    return pdf_path


def test_ocr_mode_enum():
    """Test OCRMode enum values."""
    assert OCRMode.OFF == "off"
    assert OCRMode.AUTO == "auto"
    assert OCRMode.FORCE == "force"


def test_text_block_creation():
    """Test TextBlock dataclass."""
    block = TextBlock(
        text="Hello, World!",
        bbox=(10.0, 20.0, 100.0, 40.0),
        confidence=95.5
    )
    
    assert block.text == "Hello, World!"
    assert block.bbox == (10.0, 20.0, 100.0, 40.0)
    assert block.confidence == 95.5


def test_page_text_creation():
    """Test PageText dataclass."""
    blocks = [TextBlock(text="Test text", confidence=90.0)]
    page = PageText(
        page_number=1,
        text="Test text",
        blocks=blocks,
        ocr_applied=True,
        source="ocr"
    )
    
    assert page.page_number == 1
    assert page.text == "Test text"
    assert len(page.blocks) == 1
    assert page.ocr_applied is True
    assert page.source == "ocr"


def test_processor_initialization():
    """Test OCR processor initialization."""
    # Test with OCR off (should not require tesseract)
    processor = PDFOCRProcessor(ocr_mode=OCRMode.OFF)
    assert processor.ocr_mode == OCRMode.OFF
    assert processor.low_text_threshold == 50.0
    assert processor.max_retries == 3
    assert processor.retry_delay == 1.0


def test_processor_with_auto_mode():
    """Test OCR processor with auto mode."""
    try:
        processor = PDFOCRProcessor(ocr_mode=OCRMode.AUTO)
        assert processor.ocr_mode == OCRMode.AUTO
    except RuntimeError as e:
        # Tesseract might not be available in test environment
        pytest.skip(f"Tesseract not available: {e}")


def test_processor_with_force_mode():
    """Test OCR processor with force mode."""
    try:
        processor = PDFOCRProcessor(ocr_mode=OCRMode.FORCE)
        assert processor.ocr_mode == OCRMode.FORCE
    except RuntimeError as e:
        # Tesseract might not be available in test environment
        pytest.skip(f"Tesseract not available: {e}")


def test_processor_custom_settings():
    """Test OCR processor with custom settings."""
    processor = PDFOCRProcessor(
        ocr_mode=OCRMode.OFF,
        low_text_threshold=100.0,
        max_retries=5,
        retry_delay=2.0
    )
    
    assert processor.low_text_threshold == 100.0
    assert processor.max_retries == 5
    assert processor.retry_delay == 2.0


def test_process_nonexistent_pdf():
    """Test processing a non-existent PDF file."""
    processor = PDFOCRProcessor(ocr_mode=OCRMode.OFF)
    
    with pytest.raises(FileNotFoundError):
        processor.process_pdf(Path("/nonexistent/file.pdf"))


def test_extract_text_only(simple_text_pdf):
    """Test text extraction without OCR."""
    processor = PDFOCRProcessor(ocr_mode=OCRMode.OFF)
    
    results = processor.process_pdf(simple_text_pdf)
    
    assert len(results) == 1
    assert results[0].page_number == 1
    assert results[0].ocr_applied is False
    assert results[0].source == "text_extraction"
    assert len(results[0].text) > 0
    assert "test PDF document" in results[0].text


def test_auto_process_high_text_page(simple_text_pdf):
    """Test auto-processing with a page that has sufficient text."""
    try:
        processor = PDFOCRProcessor(ocr_mode=OCRMode.AUTO, low_text_threshold=10.0)
        
        results = processor.process_pdf(simple_text_pdf)
        
        assert len(results) == 1
        assert results[0].page_number == 1
        # Should not apply OCR to page with sufficient text
        assert results[0].ocr_applied is False
        assert results[0].source == "text_extraction"
        
    except RuntimeError as e:
        pytest.skip(f"Tesseract not available: {e}")


def test_merge_texts():
    """Test text merging logic."""
    processor = PDFOCRProcessor(ocr_mode=OCRMode.OFF)
    
    # Test merging when extracted text is empty
    result = processor._merge_texts("", "OCR text")
    assert result == "OCR text"
    
    # Test merging when OCR text is empty
    result = processor._merge_texts("Extracted text", "")
    assert result == "Extracted text"
    
    # Test merging when OCR is significantly longer
    result = processor._merge_texts("Short", "This is a much longer text from OCR")
    assert "This is a much longer text from OCR" in result
    
    # Test merging when texts are similar length
    result = processor._merge_texts("Extracted", "OCR text")
    assert "Extracted" in result
    assert "OCR text" in result
    assert "[OCR Content]" in result
