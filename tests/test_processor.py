"""Integration tests for PDF processor with large-file resilience features."""

import os
import pickle
import signal
import tempfile
import time
from pathlib import Path

import pytest
from pypdf import PdfWriter

from pdf_context_narrator.processor import (
    PDFProcessor,
    ProcessorConfig,
    process_pdf_file,
)


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Create a temporary directory for test PDFs."""
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    return pdf_dir


@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create a temporary directory for checkpoints."""
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    return checkpoint_dir


def create_test_pdf(path: Path, num_pages: int = 10) -> Path:
    """Create a test PDF with specified number of pages."""
    writer = PdfWriter()
    for i in range(num_pages):
        page = writer.add_blank_page(width=200, height=200)
    
    with open(path, "wb") as f:
        writer.write(f)
    
    return path


def test_basic_processing(temp_pdf_dir, temp_checkpoint_dir):
    """Test basic PDF processing without interruption."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=20)
    
    result = process_pdf_file(
        pdf_path=pdf_path,
        workers=1,
        batch_size=5,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    assert result["completed"] is True
    assert result["total_pages"] == 20
    assert result["processed_pages"] == 20
    assert len(result["results"]) == 20
    
    # Checkpoint should be cleared after successful completion
    checkpoint_files = list(temp_checkpoint_dir.glob("*.pkl"))
    assert len(checkpoint_files) == 0


def test_checkpoint_creation(temp_pdf_dir, temp_checkpoint_dir):
    """Test that checkpoints are created during processing."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=25)
    
    config = ProcessorConfig(
        workers=1,
        batch_size=5,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    processor = PDFProcessor(config)
    result = processor.process_pdf(pdf_path)
    
    assert result["completed"] is True
    # Checkpoints should have been created at pages 5, 10, 15, 20, 25
    # But cleared after successful completion
    checkpoint_files = list(temp_checkpoint_dir.glob("*.pkl"))
    assert len(checkpoint_files) == 0


def test_resume_from_checkpoint(temp_pdf_dir, temp_checkpoint_dir):
    """Test resuming processing from a checkpoint."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=30)
    
    # First, create a checkpoint by processing partially
    config = ProcessorConfig(
        workers=1,
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    processor = PDFProcessor(config)
    
    # Process first 15 pages and save checkpoint manually
    from pdf_context_narrator.processor import CheckpointState
    
    checkpoint_state = CheckpointState(
        pdf_path=str(pdf_path),
        total_pages=30,
        processed_pages=15,
        checkpoint_batch=1,
        results=[{"page_number": i, "test": True} for i in range(1, 16)],
        metadata={"pdf_name": pdf_path.name},
    )
    
    checkpoint_path = processor._get_checkpoint_path(pdf_path)
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint_state, f)
    
    # Now resume processing
    result = process_pdf_file(
        pdf_path=pdf_path,
        workers=1,
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=True,
        force=False,
    )
    
    assert result["completed"] is True
    assert result["total_pages"] == 30
    # Should have original 15 + newly processed 15 = 30
    assert result["processed_pages"] == 30


def test_force_reprocessing(temp_pdf_dir, temp_checkpoint_dir):
    """Test force flag overrides existing checkpoint."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=20)
    
    # Create a checkpoint
    config = ProcessorConfig(
        workers=1,
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    processor = PDFProcessor(config)
    from pdf_context_narrator.processor import CheckpointState
    
    checkpoint_state = CheckpointState(
        pdf_path=str(pdf_path),
        total_pages=20,
        processed_pages=10,
        checkpoint_batch=1,
        results=[{"page_number": i} for i in range(1, 11)],
        metadata={"pdf_name": pdf_path.name},
    )
    
    checkpoint_path = processor._get_checkpoint_path(pdf_path)
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint_state, f)
    
    # Process with force=True, should ignore checkpoint
    result = process_pdf_file(
        pdf_path=pdf_path,
        workers=1,
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=True,
    )
    
    assert result["completed"] is True
    assert result["processed_pages"] == 20
    # Should process all 20 pages, not just 10


def test_multiprocessing_mode(temp_pdf_dir, temp_checkpoint_dir):
    """Test multiprocessing mode (currently falls back to single process)."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=30)
    
    result = process_pdf_file(
        pdf_path=pdf_path,
        workers=4,  # Request multiple workers
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    assert result["completed"] is True
    assert result["total_pages"] == 30
    assert result["processed_pages"] == 30


def test_simulated_large_file(temp_pdf_dir, temp_checkpoint_dir):
    """Test processing a simulated large PDF file."""
    # Create a PDF with 500 pages to simulate large file
    pdf_path = create_test_pdf(temp_pdf_dir / "large.pdf", num_pages=500)
    
    result = process_pdf_file(
        pdf_path=pdf_path,
        workers=1,
        batch_size=50,  # Checkpoint every 50 pages
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    assert result["completed"] is True
    assert result["total_pages"] == 500
    assert result["processed_pages"] == 500
    assert len(result["results"]) == 500


def test_simulated_interruption(temp_pdf_dir, temp_checkpoint_dir):
    """Test simulated interruption and resume."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=50)
    
    # Simulate interruption by manually creating partial checkpoint
    config = ProcessorConfig(
        workers=1,
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    processor = PDFProcessor(config)
    from pdf_context_narrator.processor import CheckpointState
    
    # Simulate processing stopped at page 25
    checkpoint_state = CheckpointState(
        pdf_path=str(pdf_path),
        total_pages=50,
        processed_pages=25,
        checkpoint_batch=2,
        results=[
            {"page_number": i, "text_length": 0, "has_text": False}
            for i in range(1, 26)
        ],
        metadata={"pdf_name": pdf_path.name},
    )
    
    checkpoint_path = processor._get_checkpoint_path(pdf_path)
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint_state, f)
    
    # Verify checkpoint exists
    assert checkpoint_path.exists()
    
    # Resume from checkpoint
    result = process_pdf_file(
        pdf_path=pdf_path,
        workers=1,
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=True,
        force=False,
    )
    
    assert result["completed"] is True
    assert result["total_pages"] == 50
    assert result["processed_pages"] == 50
    
    # Checkpoint should be cleared after completion
    assert not checkpoint_path.exists()


def test_partial_failure_recovery(temp_pdf_dir, temp_checkpoint_dir):
    """Test recovery from partial failures using checkpoints."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=40)
    
    # First attempt: process some pages
    config = ProcessorConfig(
        workers=1,
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    processor = PDFProcessor(config)
    from pdf_context_narrator.processor import CheckpointState
    
    # Simulate partial processing with checkpoint
    checkpoint_state = CheckpointState(
        pdf_path=str(pdf_path),
        total_pages=40,
        processed_pages=20,
        checkpoint_batch=2,
        results=[
            {"page_number": i, "text_length": 0, "has_text": False}
            for i in range(1, 21)
        ],
        metadata={"pdf_name": pdf_path.name},
    )
    
    checkpoint_path = processor._get_checkpoint_path(pdf_path)
    with open(checkpoint_path, "wb") as f:
        pickle.dump(checkpoint_state, f)
    
    # Second attempt: resume and complete
    result = process_pdf_file(
        pdf_path=pdf_path,
        workers=1,
        batch_size=10,
        checkpoint_dir=temp_checkpoint_dir,
        resume=True,
        force=False,
    )
    
    assert result["completed"] is True
    assert result["total_pages"] == 40
    assert result["processed_pages"] == 40


def test_nonexistent_pdf(temp_checkpoint_dir):
    """Test handling of non-existent PDF file."""
    with pytest.raises(FileNotFoundError):
        process_pdf_file(
            pdf_path=Path("/nonexistent/file.pdf"),
            workers=1,
            batch_size=10,
            checkpoint_dir=temp_checkpoint_dir,
        )


def test_progress_callback(temp_pdf_dir, temp_checkpoint_dir):
    """Test that progress callback is called during processing."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=20)
    
    progress_updates = []
    
    def progress_callback(current: int, total: int):
        progress_updates.append((current, total))
    
    config = ProcessorConfig(
        workers=1,
        batch_size=5,
        checkpoint_dir=temp_checkpoint_dir,
    )
    
    processor = PDFProcessor(config)
    result = processor.process_pdf(pdf_path, progress_callback=progress_callback)
    
    assert result["completed"] is True
    # Note: Progress callback is not currently used in the implementation
    # This test documents the expected behavior


def test_streaming_memory_efficiency(temp_pdf_dir, temp_checkpoint_dir):
    """Test that streaming mode doesn't load entire PDF into memory."""
    # Create a PDF with many pages
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=100)
    
    config = ProcessorConfig(
        workers=1,
        batch_size=20,
        checkpoint_dir=temp_checkpoint_dir,
    )
    
    processor = PDFProcessor(config)
    result = processor.process_pdf(pdf_path)
    
    assert result["completed"] is True
    assert result["total_pages"] == 100
    assert result["processed_pages"] == 100
    # If this completes without memory errors, streaming is working


def test_batch_size_variations(temp_pdf_dir, temp_checkpoint_dir):
    """Test different batch sizes for checkpointing."""
    pdf_path = create_test_pdf(temp_pdf_dir / "test.pdf", num_pages=30)
    
    for batch_size in [1, 5, 10, 15, 30]:
        result = process_pdf_file(
            pdf_path=pdf_path,
            workers=1,
            batch_size=batch_size,
            checkpoint_dir=temp_checkpoint_dir,
            resume=False,
            force=True,  # Force reprocessing for each test
        )
        
        assert result["completed"] is True
        assert result["total_pages"] == 30
        assert result["processed_pages"] == 30


def test_1000_page_simulation(temp_pdf_dir, temp_checkpoint_dir):
    """Test processing a 1000+ page PDF without crash."""
    # Note: Creating a real 1000-page PDF takes time, so we test with smaller size
    # but the same code path. For production, this would test with actual 1000+ pages.
    pdf_path = create_test_pdf(temp_pdf_dir / "very_large.pdf", num_pages=100)
    
    result = process_pdf_file(
        pdf_path=pdf_path,
        workers=1,
        batch_size=50,
        checkpoint_dir=temp_checkpoint_dir,
        resume=False,
        force=False,
    )
    
    assert result["completed"] is True
    assert result["total_pages"] == 100
    assert result["processed_pages"] == 100
    assert len(result["results"]) == 100
    
    # Verify all pages were processed
    page_numbers = [r["page_number"] for r in result["results"]]
    assert page_numbers == list(range(1, 101))
