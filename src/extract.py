"""
Text extraction from PDF files with pypdf and pdfplumber fallback.

This module provides functions for extracting text from PDF pages using 
multiple extraction methods with fallback support.
"""
import logging
from pathlib import Path
from typing import Optional, Union

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

logger = logging.getLogger(__name__)


def extract_text_pypdf(pdf_path: Union[str, Path], page_num: int) -> Optional[str]:
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


def extract_text_pdfplumber(pdf_path: Union[str, Path], page_num: int) -> Optional[str]:
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


def extract_text(pdf_path: Union[str, Path], page_num: int) -> tuple[Optional[str], str]:
    """
    Extract text from a PDF page with automatic fallback.

    Args:
        pdf_path: Path to the PDF file
        page_num: Page number (0-indexed)

    Returns:
        Tuple of (extracted text, extraction method used)
        Text will be None if both methods fail
    """
    # Try pypdf first
    text = extract_text_pypdf(pdf_path, page_num)
    if text is not None:
        return text, "pypdf"
    
    # Fall back to pdfplumber
    text = extract_text_pdfplumber(pdf_path, page_num)
    if text is not None:
        return text, "pdfplumber"
    
    logger.error(f"Both extraction methods failed for {pdf_path} page {page_num}")
    return None, "none"
