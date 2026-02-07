"""Tests for CLI commands."""

import pytest
import tempfile
from pathlib import Path
from typer.testing import CliRunner

from pdf_context_narrator.cli import app

# Try to import reportlab for creating test PDFs
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_pdf(temp_dir):
    """Create a sample PDF for testing."""
    if not REPORTLAB_AVAILABLE:
        pytest.skip("reportlab not available for creating test PDFs")
    
    pdf_path = temp_dir / "test.pdf"
    
    # Create a simple PDF
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.drawString(100, 750, "This is a test PDF document for CLI testing.")
    c.drawString(100, 730, "It contains some sample text content.")
    c.showPage()
    c.save()
    
    return pdf_path


def test_ingest_command_with_pdf(sample_pdf):
    """Test the ingest command with a real PDF file."""
    result = runner.invoke(app, ["ingest", str(sample_pdf), "--ocr-mode", "off"])
    assert result.exit_code == 0
    assert "Ingesting PDFs" in result.stdout
    assert "Processed 1 page(s)" in result.stdout


def test_ingest_command_with_ocr_auto(sample_pdf):
    """Test the ingest command with auto OCR mode."""
    result = runner.invoke(app, ["ingest", str(sample_pdf), "--ocr-mode", "auto"])
    assert result.exit_code == 0
    assert "OCR mode: auto" in result.stdout


def test_ingest_command_nonexistent_file():
    """Test the ingest command with a non-existent file."""
    result = runner.invoke(app, ["ingest", "nonexistent.pdf"])
    assert result.exit_code == 1
    assert "does not exist" in result.stdout


def test_ingest_command_directory(temp_dir):
    """Test the ingest command with a directory containing no PDFs."""
    result = runner.invoke(app, ["ingest", str(temp_dir)])
    assert result.exit_code == 1
    assert "No PDF files found" in result.stdout


def test_search_command():
    """Test the search command."""
    result = runner.invoke(app, ["search", "test query"])
    assert result.exit_code == 0
    assert "Searching for" in result.stdout


def test_summarize_command():
    """Test the summarize command."""
    result = runner.invoke(app, ["summarize", "test.pdf"])
    assert result.exit_code == 0
    assert "Summarizing document" in result.stdout


def test_timeline_command():
    """Test the timeline command."""
    result = runner.invoke(app, ["timeline"])
    assert result.exit_code == 0
    assert "Generating timeline" in result.stdout


def test_export_command():
    """Test the export command."""
    result = runner.invoke(app, ["export", "json", "output.json"])
    assert result.exit_code == 0
    assert "Exporting data" in result.stdout


def test_help_command():
    """Test help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "A tool for ingesting, searching, and analyzing PDF documents" in result.stdout
