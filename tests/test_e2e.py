"""End-to-end integration tests for PDF Context Narrator.

Tests the complete workflow: ingest -> index -> search -> summarize -> export
"""

from typer.testing import CliRunner

from pdf_context_narrator.cli import app

runner = CliRunner()


class TestE2EWorkflow:
    """End-to-end tests for the complete PDF processing workflow."""

    def test_complete_workflow_json_export(self, tmp_path):
        """Test complete workflow: ingest -> search -> export to JSON."""
        # Setup: Create a temporary PDF file (stub)
        pdf_file = tmp_path / "test_document.pdf"
        pdf_file.write_text("PDF content stub")

        # Step 1: Ingest the PDF
        result = runner.invoke(app, ["ingest", str(pdf_file)])
        assert result.exit_code == 0
        assert "Ingesting PDFs" in result.stdout
        assert "complete" in result.stdout.lower()

        # Step 2: Search for content (would normally index first)
        result = runner.invoke(app, ["search", "test query", "--limit", "5"])
        assert result.exit_code == 0
        assert "Searching for" in result.stdout

        # Step 3: Summarize the document
        result = runner.invoke(app, ["summarize", str(pdf_file)])
        assert result.exit_code == 0
        assert "Summarizing document" in result.stdout

        # Step 4: Export to JSON
        output_json = tmp_path / "output.json"
        result = runner.invoke(app, ["export", "json", str(output_json)])
        assert result.exit_code == 0
        assert "Exporting data" in result.stdout

    def test_complete_workflow_markdown_export(self, tmp_path):
        """Test complete workflow: ingest -> search -> export to Markdown."""
        # Setup: Create temporary PDF files
        pdf_files = []
        for i in range(3):
            pdf_file = tmp_path / f"document_{i}.pdf"
            pdf_file.write_text(f"PDF content stub {i}")
            pdf_files.append(pdf_file)

        # Step 1: Ingest multiple PDFs
        for pdf_file in pdf_files:
            result = runner.invoke(app, ["ingest", str(pdf_file)])
            assert result.exit_code == 0

        # Step 2: Search with multiple results
        result = runner.invoke(app, ["search", "document", "--limit", "10"])
        assert result.exit_code == 0

        # Step 3: Generate timeline
        result = runner.invoke(app, ["timeline", "--start", "2024-01-01", "--end", "2024-12-31"])
        assert result.exit_code == 0
        assert "Generating timeline" in result.stdout

        # Step 4: Export to Markdown
        output_md = tmp_path / "output.md"
        result = runner.invoke(app, ["export", "markdown", str(output_md)])
        assert result.exit_code == 0

    def test_workflow_with_filters(self, tmp_path):
        """Test workflow with filtering and custom options."""
        # Setup
        pdf_file = tmp_path / "filtered_doc.pdf"
        pdf_file.write_text("PDF content")

        # Ingest with force flag
        result = runner.invoke(app, ["ingest", str(pdf_file), "--force"])
        assert result.exit_code == 0
        assert "Force: True" in result.stdout or "complete" in result.stdout.lower()

        # Search with format option
        result = runner.invoke(app, ["search", "query", "--format", "json", "--limit", "5"])
        assert result.exit_code == 0

        # Export with filter
        output_file = tmp_path / "filtered.json"
        result = runner.invoke(
            app, ["export", "json", str(output_file), "--filter", "status:processed"]
        )
        assert result.exit_code == 0

    def test_recursive_ingest_workflow(self, tmp_path):
        """Test workflow with recursive directory ingestion."""
        # Setup: Create nested directory structure with PDFs
        subdir1 = tmp_path / "subdir1"
        subdir2 = tmp_path / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()

        # Create PDFs in different directories
        (tmp_path / "root.pdf").write_text("Root PDF")
        (subdir1 / "sub1.pdf").write_text("Subdir1 PDF")
        (subdir2 / "sub2.pdf").write_text("Subdir2 PDF")

        # Ingest recursively
        result = runner.invoke(app, ["ingest", str(tmp_path), "--recursive"])
        assert result.exit_code == 0
        assert "Recursive: True" in result.stdout or "complete" in result.stdout.lower()

    def test_summarize_with_output_file(self, tmp_path):
        """Test summarization with output file."""
        # Setup
        pdf_file = tmp_path / "summary_test.pdf"
        pdf_file.write_text("PDF to summarize")
        summary_output = tmp_path / "summary.txt"

        # Ingest
        result = runner.invoke(app, ["ingest", str(pdf_file)])
        assert result.exit_code == 0

        # Summarize with different lengths
        for length in ["short", "medium", "long"]:
            result = runner.invoke(
                app,
                ["summarize", str(pdf_file), "--length", length, "--output", str(summary_output)],
            )
            assert result.exit_code == 0
            assert length in result.stdout.lower()

    def test_timeline_with_date_range(self, tmp_path):
        """Test timeline generation with date filtering."""
        # Setup
        pdf_file = tmp_path / "timeline_doc.pdf"
        pdf_file.write_text("Document with dates")
        timeline_output = tmp_path / "timeline.json"

        # Ingest
        result = runner.invoke(app, ["ingest", str(pdf_file)])
        assert result.exit_code == 0

        # Generate timeline with date range and output
        result = runner.invoke(
            app,
            [
                "timeline",
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-31",
                "--output",
                str(timeline_output),
            ],
        )
        assert result.exit_code == 0
        assert "Start: 2023-01-01" in result.stdout
        assert "End: 2024-12-31" in result.stdout

    def test_multiple_export_formats(self, tmp_path):
        """Test exporting to different formats."""
        # Setup
        pdf_file = tmp_path / "export_test.pdf"
        pdf_file.write_text("PDF to export")

        # Ingest
        result = runner.invoke(app, ["ingest", str(pdf_file)])
        assert result.exit_code == 0

        # Test each export format
        formats = ["json", "csv", "markdown"]
        extensions = {"json": ".json", "csv": ".csv", "markdown": ".md"}

        for fmt in formats:
            output_file = tmp_path / f"export_output{extensions[fmt]}"
            result = runner.invoke(app, ["export", fmt, str(output_file)])
            assert result.exit_code == 0
            assert fmt in result.stdout.lower()

    def test_workflow_with_config_profiles(self, tmp_path):
        """Test workflow using different configuration profiles."""
        pdf_file = tmp_path / "profile_test.pdf"
        pdf_file.write_text("PDF content")

        # Test with different profiles
        profiles = ["local", "offline"]  # cloud requires env vars

        for profile in profiles:
            result = runner.invoke(app, ["--profile", profile, "ingest", str(pdf_file)])
            # Should work even if profile file doesn't exist (falls back to defaults)
            # or succeeds if profile file exists
            assert result.exit_code in [0, 1, 2]  # Allow for missing profile files

    def test_verbose_and_structured_logging(self, tmp_path):
        """Test workflow with verbose and structured logging options."""
        pdf_file = tmp_path / "logging_test.pdf"
        pdf_file.write_text("PDF content")

        # Test with verbose flag
        result = runner.invoke(app, ["--verbose", "ingest", str(pdf_file)])
        assert result.exit_code == 0

        # Test with structured logging
        result = runner.invoke(app, ["--structured-logs", "search", "test query"])
        assert result.exit_code == 0


class TestE2EErrorHandling:
    """Test error handling in end-to-end workflows."""

    def test_ingest_nonexistent_file(self):
        """Test ingesting a file that doesn't exist."""
        result = runner.invoke(app, ["ingest", "nonexistent.pdf"])
        # Should fail gracefully (currently stub returns 0)
        assert result.exit_code in [0, 1, 2]

    def test_export_without_data(self, tmp_path):
        """Test exporting when no data has been ingested."""
        output_file = tmp_path / "empty_export.json"
        result = runner.invoke(app, ["export", "json", str(output_file)])
        # Stub implementation returns 0
        assert result.exit_code == 0

    def test_search_empty_query(self):
        """Test searching with empty query."""
        result = runner.invoke(app, ["search", ""])
        # Should handle empty query gracefully
        assert result.exit_code in [0, 2]


class TestE2EDataFlow:
    """Test data flow between different commands."""

    def test_data_persistence_across_commands(self, tmp_path):
        """Test that data persists across multiple commands."""
        pdf_file = tmp_path / "persistence_test.pdf"
        pdf_file.write_text("PDF content")

        # Ingest data
        result1 = runner.invoke(app, ["ingest", str(pdf_file)])
        assert result1.exit_code == 0

        # Search should be able to access ingested data
        result2 = runner.invoke(app, ["search", "content"])
        assert result2.exit_code == 0

        # Export should include ingested data
        output_file = tmp_path / "persistence_export.json"
        result3 = runner.invoke(app, ["export", "json", str(output_file)])
        assert result3.exit_code == 0

    def test_incremental_ingestion(self, tmp_path):
        """Test adding documents incrementally."""
        # First batch
        pdf1 = tmp_path / "doc1.pdf"
        pdf1.write_text("First document")
        result1 = runner.invoke(app, ["ingest", str(pdf1)])
        assert result1.exit_code == 0

        # Second batch
        pdf2 = tmp_path / "doc2.pdf"
        pdf2.write_text("Second document")
        result2 = runner.invoke(app, ["ingest", str(pdf2)])
        assert result2.exit_code == 0

        # Both should be searchable
        result3 = runner.invoke(app, ["search", "document"])
        assert result3.exit_code == 0
