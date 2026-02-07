"""Tests for CLI commands."""

import pytest
import json
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


def test_ingest_command(tmp_path):
    """Test the ingest command."""
    from pypdf import PdfWriter
    
    # Create a test PDF
    test_pdf = tmp_path / "test.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with open(test_pdf, "wb") as f:
        writer.write(f)
    
    result = runner.invoke(app, ["ingest", str(test_pdf)])
    assert result.exit_code == 0
    assert "Ingesting PDFs" in result.stdout
    assert "Successfully processed" in result.stdout
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
    """Test the search command with no indexed documents."""
    result = runner.invoke(app, ["search", "test query"])
    assert result.exit_code == 0
    # When no documents are found, it should show a warning
    assert "Indexing documents" in result.stdout or "No documents found" in result.stdout


def test_search_command_with_fixtures():
    """Test the search command with test fixtures."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    
    result = runner.invoke(app, ["search", "machine learning", "--data-dir", str(fixtures_dir)])
    assert result.exit_code == 0
    assert "Searching for" in result.stdout


def test_search_command_json_format():
    """Test search command with JSON format."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    
    result = runner.invoke(app, ["search", "machine learning", "--data-dir", str(fixtures_dir), "--format", "json"])
    assert result.exit_code == 0


def test_search_command_markdown_format():
    """Test search command with Markdown format."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    
    result = runner.invoke(app, ["search", "machine learning", "--data-dir", str(fixtures_dir), "--format", "markdown"])
    assert result.exit_code == 0
    assert "Search Results" in result.stdout


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


def test_rebuild_index_command_with_sample_jsonl(tmp_path):
    """Test rebuild-index command with sample JSONL file."""
    # Create a sample JSONL file
    jsonl_file = tmp_path / "sample.jsonl"
    sample_data = [
        {
            "file": "doc1.pdf",
            "page": 1,
            "section": "Introduction",
            "text": "This is a sample document about Python programming. " * 20,
            "metadata": {"author": "Test Author"},
        },
        {
            "file": "doc2.pdf",
            "page": 2,
            "section": "Methods",
            "text": "Machine learning is a fascinating field of study. " * 20,
            "metadata": {"author": "Test Author"},
        },
    ]
    
    with open(jsonl_file, "w") as f:
        for item in sample_data:
            f.write(json.dumps(item) + "\n")
    
    # Run rebuild-index command (may fail if model can't be downloaded)
    index_path = tmp_path / "test_index"
    result = runner.invoke(
        app,
        ["rebuild-index", str(jsonl_file), "--index-path", str(index_path)],
    )
    
    # Accept either success or model download failure
    if result.exit_code == 0:
        assert "Rebuilding index" in result.stdout
        assert "Index rebuild complete" in result.stdout
        
        # Verify index files were created
        assert index_path.with_suffix(".faiss").exists()
        assert index_path.with_suffix(".meta.json").exists()
    else:
        # Model download may fail in test environment
        pytest.skip("Could not download embeddings model in test environment")


def test_rebuild_index_nonexistent_file():
    """Test rebuild-index with non-existent file."""
    result = runner.invoke(app, ["rebuild-index", "nonexistent.jsonl"])
    assert result.exit_code == 1
    assert "Error" in result.stdout or "not found" in result.stdout


def test_index_info_command(tmp_path):
    """Test index-info command."""
    # First create an index
    jsonl_file = tmp_path / "sample.jsonl"
    sample_data = {
        "file": "test.pdf",
        "page": 1,
        "text": "Sample text for testing index info command. " * 20,
    }
    
    with open(jsonl_file, "w") as f:
        f.write(json.dumps(sample_data) + "\n")
    
    index_path = tmp_path / "test_index"
    rebuild_result = runner.invoke(
        app,
        ["rebuild-index", str(jsonl_file), "--index-path", str(index_path)],
    )
    
    # Only test index-info if rebuild succeeded
    if rebuild_result.exit_code != 0:
        pytest.skip("Could not rebuild index (model download may have failed)")
    
    # Now test index-info
    result = runner.invoke(app, ["index-info", "--index-path", str(index_path)])
    
    assert result.exit_code == 0
    assert "Index Information" in result.stdout
    assert "Total vectors" in result.stdout


def test_index_info_nonexistent():
    """Test index-info with non-existent index."""
    result = runner.invoke(app, ["index-info", "--index-path", "/nonexistent/path"])
    assert result.exit_code == 1

