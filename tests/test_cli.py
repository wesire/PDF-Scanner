"""Tests for CLI commands."""

import pytest
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
