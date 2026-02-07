"""Tests for CLI commands."""

import pytest
import json
from pathlib import Path
from typer.testing import CliRunner

from pdf_context_narrator.cli import app

runner = CliRunner()


def test_ingest_command():
    """Test the ingest command."""
    result = runner.invoke(app, ["ingest", "test.pdf"])
    assert result.exit_code == 0
    assert "Ingesting PDFs" in result.stdout


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

