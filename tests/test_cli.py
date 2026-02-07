"""Tests for CLI commands."""

import pytest
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
