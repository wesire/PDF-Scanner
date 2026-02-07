"""
PDF Text Extractor with pypdf primary and pdfplumber fallback.

This module extracts text from PDF files with per-page metadata and graceful error handling.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """Extract text from PDF files with fallback support."""

    def __init__(self, output_dir: Union[str, Path] = "data/extracted"):
        """
        Initialize PDF text extractor.

        Args:
            output_dir: Directory to save extracted text JSONL files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_pypdf(self, pdf_path: Union[str, Path], page_num: int) -> Optional[str]:
        """
        Extract text from a PDF page using pypdf.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)

        Returns:
            Extracted text or None if extraction fails
        """
        if pypdf is None:
            logger.warning("pypdf not installed, skipping pypdf extraction")
            return None

        try:
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                # Check if file is encrypted
                if reader.is_encrypted:
                    logger.warning(f"PDF {pdf_path} is encrypted, cannot extract with pypdf")
                    return None
                
                if page_num >= len(reader.pages):
                    logger.warning(f"Page {page_num} out of range for {pdf_path}")
                    return None
                
                page = reader.pages[page_num]
                text = page.extract_text()
                return text if text else None
                
        except Exception as e:
            logger.warning(f"pypdf extraction failed for {pdf_path} page {page_num}: {e}")
            return None

    def extract_text_pdfplumber(self, pdf_path: Union[str, Path], page_num: int) -> Optional[str]:
        """
        Extract text from a PDF page using pdfplumber (fallback).

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)

        Returns:
            Extracted text or None if extraction fails
        """
        if pdfplumber is None:
            logger.warning("pdfplumber not installed, cannot use fallback")
            return None

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num >= len(pdf.pages):
                    logger.warning(f"Page {page_num} out of range for {pdf_path}")
                    return None
                
                page = pdf.pages[page_num]
                text = page.extract_text()
                return text if text else None
                
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed for {pdf_path} page {page_num}: {e}")
            return None

    def extract_page(self, pdf_path: Union[str, Path], page_num: int) -> Optional[Dict]:
        """
        Extract text from a single PDF page with metadata.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)

        Returns:
            Dictionary with file, page, chars, extraction_method, and text
        """
        pdf_path = Path(pdf_path)
        
        # Try pypdf first
        text = self.extract_text_pypdf(pdf_path, page_num)
        extraction_method = "pypdf"
        
        # Fall back to pdfplumber if pypdf fails
        if text is None:
            text = self.extract_text_pdfplumber(pdf_path, page_num)
            extraction_method = "pdfplumber"
        
        # If both fail, return None
        if text is None:
            logger.error(f"Both extraction methods failed for {pdf_path} page {page_num}")
            return None
        
        return {
            "file": str(pdf_path.absolute()),
            "page": page_num,
            "chars": len(text),
            "extraction_method": extraction_method,
            "text": text
        }

    def get_page_count(self, pdf_path: Union[str, Path]) -> Optional[int]:
        """
        Get the number of pages in a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Number of pages or None if unable to determine
        """
        pdf_path = Path(pdf_path)
        
        # Try pypdf first
        if pypdf is not None:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = pypdf.PdfReader(file)
                    if reader.is_encrypted:
                        try:
                            reader.decrypt('')
                        except Exception as e:
                            logger.debug(f"Failed to decrypt {pdf_path}: {e}")
                    return len(reader.pages)
            except Exception as e:
                logger.warning(f"pypdf page count failed for {pdf_path}: {e}")
        
        # Fall back to pdfplumber
        if pdfplumber is not None:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    return len(pdf.pages)
            except Exception as e:
                logger.warning(f"pdfplumber page count failed for {pdf_path}: {e}")
        
        return None

    def extract_pdf(self, pdf_path: Union[str, Path]) -> List[Dict]:
        """
        Extract text from all pages in a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of dictionaries with extracted text and metadata
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return []
        
        page_count = self.get_page_count(pdf_path)
        if page_count is None:
            logger.error(f"Unable to determine page count for {pdf_path}")
            return []
        
        logger.info(f"Extracting {page_count} pages from {pdf_path}")
        
        results = []
        for page_num in range(page_count):
            page_data = self.extract_page(pdf_path, page_num)
            if page_data is not None:
                results.append(page_data)
            else:
                logger.warning(f"Skipping page {page_num} of {pdf_path} due to extraction failure")
        
        return results

    def save_to_jsonl(self, data: List[Dict], output_filename: str) -> Path:
        """
        Save extracted data to a JSONL file.

        Args:
            data: List of dictionaries with extracted text and metadata
            output_filename: Name of the output JSONL file

        Returns:
            Path to the saved JSONL file
        """
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
        
        logger.info(f"Saved {len(data)} pages to {output_path}")
        return output_path

    def process_pdf(self, pdf_path: Union[str, Path], output_filename: Optional[str] = None) -> Path:
        """
        Process a PDF file and save extracted text to JSONL.

        Args:
            pdf_path: Path to the PDF file
            output_filename: Optional output filename (defaults to PDF filename + .jsonl)

        Returns:
            Path to the saved JSONL file
        """
        pdf_path = Path(pdf_path)
        
        if output_filename is None:
            output_filename = f"{pdf_path.stem}.jsonl"
        
        extracted_data = self.extract_pdf(pdf_path)
        
        if not extracted_data:
            logger.warning(f"No data extracted from {pdf_path}")
        
        return self.save_to_jsonl(extracted_data, output_filename)
