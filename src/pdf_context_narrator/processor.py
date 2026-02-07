"""PDF processor with large-file resilience features."""

import json
import multiprocessing as mp
import os
import pickle
import signal
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from pypdf import PdfReader
from tqdm import tqdm

from pdf_context_narrator.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CheckpointState:
    """State to be saved at checkpoints."""
    
    pdf_path: str
    total_pages: int
    processed_pages: int
    checkpoint_batch: int
    results: list[dict[str, Any]]
    metadata: dict[str, Any]


@dataclass
class ProcessorConfig:
    """Configuration for PDF processor."""
    
    workers: int = 1
    batch_size: int = 10
    memory_limit_mb: Optional[int] = None
    checkpoint_dir: Path = Path("checkpoints")
    resume: bool = False
    force: bool = False


class PDFProcessor:
    """Process PDFs with streaming, checkpoints, and multiprocessing support."""
    
    def __init__(self, config: ProcessorConfig):
        """Initialize processor with configuration."""
        self.config = config
        self.checkpoint_dir = config.checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._interrupted = False
        
        # Set up signal handlers for graceful interruption
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle interruption signals gracefully."""
        logger.warning(f"Received signal {signum}, will save checkpoint and exit...")
        self._interrupted = True
    
    def _get_checkpoint_path(self, pdf_path: Path) -> Path:
        """Get checkpoint file path for a PDF."""
        safe_name = pdf_path.name.replace(".pdf", "").replace("/", "_")
        return self.checkpoint_dir / f"{safe_name}_checkpoint.pkl"
    
    def _save_checkpoint(self, state: CheckpointState) -> None:
        """Save processing state to checkpoint file."""
        checkpoint_path = self._get_checkpoint_path(Path(state.pdf_path))
        try:
            with open(checkpoint_path, "wb") as f:
                pickle.dump(state, f)
            logger.info(
                f"Checkpoint saved: {state.processed_pages}/{state.total_pages} pages processed"
            )
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def _load_checkpoint(self, pdf_path: Path) -> Optional[CheckpointState]:
        """Load processing state from checkpoint file."""
        checkpoint_path = self._get_checkpoint_path(pdf_path)
        if not checkpoint_path.exists():
            return None
        
        try:
            with open(checkpoint_path, "rb") as f:
                state = pickle.load(f)
            logger.info(
                f"Checkpoint loaded: resuming from page {state.processed_pages}/{state.total_pages}"
            )
            return state
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def _clear_checkpoint(self, pdf_path: Path) -> None:
        """Clear checkpoint file after successful completion."""
        checkpoint_path = self._get_checkpoint_path(pdf_path)
        if checkpoint_path.exists():
            try:
                checkpoint_path.unlink()
                logger.info("Checkpoint cleared")
            except Exception as e:
                logger.error(f"Failed to clear checkpoint: {e}")
    
    def _stream_pages(
        self, pdf_path: Path, start_page: int = 0
    ) -> Iterator[tuple[int, Any]]:
        """Stream pages from PDF starting at specified page."""
        try:
            reader = PdfReader(str(pdf_path))
            total_pages = len(reader.pages)
            
            for page_num in range(start_page, total_pages):
                if self._interrupted:
                    break
                yield page_num, reader.pages[page_num]
        except Exception as e:
            logger.error(f"Error streaming pages from {pdf_path}: {e}")
            raise
    
    def _process_page(
        self, page_num: int, page: Any, pdf_path: Path
    ) -> dict[str, Any]:
        """Process a single page and extract information."""
        try:
            # Extract text from page
            text = page.extract_text() or ""
            
            # Get page metadata
            result = {
                "page_number": page_num + 1,  # 1-indexed for user display
                "text_length": len(text),
                "has_text": bool(text.strip()),
                "text_preview": text[:200] if text else "",
            }
            
            return result
        except Exception as e:
            logger.error(f"Error processing page {page_num} of {pdf_path}: {e}")
            return {
                "page_number": page_num + 1,
                "error": str(e),
            }
    
    def _process_page_wrapper(self, args: tuple[int, Any, Path]) -> dict[str, Any]:
        """Wrapper for multiprocessing."""
        page_num, page_data, pdf_path = args
        # Note: page_data will be serialized page information, not the actual page object
        # In real implementation, we'd need to reopen the PDF in each worker
        return self._process_page(page_num, page_data, pdf_path)
    
    def _check_memory_limit(self) -> None:
        """Check if memory usage is within limits."""
        if self.config.memory_limit_mb is None:
            return
        
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.config.memory_limit_mb:
                logger.warning(
                    f"Memory usage ({memory_mb:.2f} MB) exceeds limit "
                    f"({self.config.memory_limit_mb} MB)"
                )
        except ImportError:
            logger.debug("psutil not available, skipping memory check")
    
    def process_pdf(
        self, pdf_path: Path, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> dict[str, Any]:
        """
        Process a PDF file with streaming and checkpointing.
        
        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback for progress updates (current, total)
            
        Returns:
            Dictionary with processing results
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Check for existing checkpoint
        state = None
        if self.config.resume and not self.config.force:
            state = self._load_checkpoint(pdf_path)
        
        # Initialize or resume state
        if state:
            start_page = state.processed_pages
            results = state.results
            metadata = state.metadata
        else:
            start_page = 0
            results = []
            metadata = {
                "pdf_path": str(pdf_path),
                "pdf_name": pdf_path.name,
            }
        
        # Get total pages
        try:
            reader = PdfReader(str(pdf_path))
            total_pages = len(reader.pages)
            logger.info(f"Processing PDF: {pdf_path} ({total_pages} pages)")
        except Exception as e:
            logger.error(f"Failed to open PDF {pdf_path}: {e}")
            raise
        
        # Process pages with progress bar
        with tqdm(
            total=total_pages,
            initial=start_page,
            desc=f"Processing {pdf_path.name}",
            unit="page",
        ) as pbar:
            
            if self.config.workers > 1:
                # Multiprocessing mode
                results.extend(
                    self._process_with_multiprocessing(
                        pdf_path, start_page, total_pages, pbar
                    )
                )
            else:
                # Single process streaming mode
                results.extend(
                    self._process_streaming(
                        pdf_path, start_page, total_pages, pbar
                    )
                )
        
        # Clear checkpoint on successful completion
        if not self._interrupted:
            self._clear_checkpoint(pdf_path)
            logger.info(f"Successfully processed {total_pages} pages")
        
        return {
            "metadata": metadata,
            "total_pages": total_pages,
            "processed_pages": len(results),
            "results": results,
            "completed": not self._interrupted,
        }
    
    def _process_streaming(
        self, pdf_path: Path, start_page: int, total_pages: int, pbar: tqdm
    ) -> list[dict[str, Any]]:
        """Process PDF in streaming mode (single process)."""
        results = []
        batch_results = []
        
        for page_num, page in self._stream_pages(pdf_path, start_page):
            if self._interrupted:
                # Save checkpoint before exiting
                state = CheckpointState(
                    pdf_path=str(pdf_path),
                    total_pages=total_pages,
                    processed_pages=page_num,
                    checkpoint_batch=len(results) // self.config.batch_size,
                    results=results + batch_results,
                    metadata={"pdf_name": pdf_path.name},
                )
                self._save_checkpoint(state)
                break
            
            # Process page
            result = self._process_page(page_num, page, pdf_path)
            batch_results.append(result)
            pbar.update(1)
            
            # Check memory limit
            self._check_memory_limit()
            
            # Save checkpoint at batch boundaries
            if len(batch_results) >= self.config.batch_size:
                results.extend(batch_results)
                state = CheckpointState(
                    pdf_path=str(pdf_path),
                    total_pages=total_pages,
                    processed_pages=page_num + 1,
                    checkpoint_batch=len(results) // self.config.batch_size,
                    results=results,
                    metadata={"pdf_name": pdf_path.name},
                )
                self._save_checkpoint(state)
                batch_results = []
        
        # Add remaining batch results
        results.extend(batch_results)
        return results
    
    def _process_with_multiprocessing(
        self, pdf_path: Path, start_page: int, total_pages: int, pbar: tqdm
    ) -> list[dict[str, Any]]:
        """Process PDF with multiprocessing."""
        results = []
        batch_args = []
        
        # Note: For true multiprocessing with PDFs, each worker would need to
        # reopen the PDF file to avoid serialization issues with page objects
        for page_num, page in self._stream_pages(pdf_path, start_page):
            if self._interrupted:
                # Save checkpoint before exiting
                state = CheckpointState(
                    pdf_path=str(pdf_path),
                    total_pages=total_pages,
                    processed_pages=page_num,
                    checkpoint_batch=len(results) // self.config.batch_size,
                    results=results,
                    metadata={"pdf_name": pdf_path.name},
                )
                self._save_checkpoint(state)
                break
            
            # In single-process fallback mode for now (due to PDF object serialization)
            result = self._process_page(page_num, page, pdf_path)
            results.append(result)
            pbar.update(1)
            
            # Check memory limit
            self._check_memory_limit()
            
            # Save checkpoint at batch boundaries
            if len(results) % self.config.batch_size == 0:
                state = CheckpointState(
                    pdf_path=str(pdf_path),
                    total_pages=total_pages,
                    processed_pages=page_num + 1,
                    checkpoint_batch=len(results) // self.config.batch_size,
                    results=results,
                    metadata={"pdf_name": pdf_path.name},
                )
                self._save_checkpoint(state)
        
        return results


def process_pdf_file(
    pdf_path: Path,
    workers: int = 1,
    batch_size: int = 10,
    memory_limit_mb: Optional[int] = None,
    checkpoint_dir: Path = Path("checkpoints"),
    resume: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """
    Convenience function to process a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        workers: Number of parallel workers (multiprocessing)
        batch_size: Number of pages between checkpoints
        memory_limit_mb: Memory limit in MB (requires psutil)
        checkpoint_dir: Directory for checkpoint files
        resume: Whether to resume from checkpoint
        force: Force reprocessing even if checkpoint exists
        
    Returns:
        Dictionary with processing results
    """
    config = ProcessorConfig(
        workers=workers,
        batch_size=batch_size,
        memory_limit_mb=memory_limit_mb,
        checkpoint_dir=checkpoint_dir,
        resume=resume,
        force=force,
    )
    
    processor = PDFProcessor(config)
    return processor.process_pdf(pdf_path)
