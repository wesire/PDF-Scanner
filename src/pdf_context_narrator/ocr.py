"""OCR module for extracting text from scanned pages and images."""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple
import time

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader

from pdf_context_narrator.logger import get_logger

logger = get_logger(__name__)


class OCRMode(str, Enum):
    """OCR processing modes."""
    OFF = "off"
    AUTO = "auto"
    FORCE = "force"


@dataclass
class TextBlock:
    """A block of text with its bounding box and confidence score."""
    text: str
    bbox: Optional[Tuple[float, float, float, float]] = None  # (x0, y0, x1, y1)
    confidence: Optional[float] = None  # 0-100 confidence score


@dataclass
class PageText:
    """Text extracted from a single page."""
    page_number: int
    text: str
    blocks: List[TextBlock]
    ocr_applied: bool
    source: str  # "text_extraction", "ocr", or "hybrid"


class PDFOCRProcessor:
    """Process PDFs with OCR capabilities for scanned documents."""
    
    def __init__(
        self,
        ocr_mode: OCRMode = OCRMode.AUTO,
        low_text_threshold: float = 50.0,  # Minimum chars per page for "normal" text
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the PDF OCR processor.
        
        Args:
            ocr_mode: OCR processing mode (off/auto/force)
            low_text_threshold: Minimum character count to consider a page as having text
            max_retries: Maximum number of retries for OCR operations
            retry_delay: Delay between retries in seconds
        """
        self.ocr_mode = ocr_mode
        self.low_text_threshold = low_text_threshold
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Verify tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            logger.error(f"Tesseract not found or not working: {e}")
            if self.ocr_mode != OCRMode.OFF:
                raise RuntimeError("Tesseract is required for OCR but not available") from e
    
    def process_pdf(self, pdf_path: Path) -> List[PageText]:
        """
        Process a PDF and extract text with OCR as needed.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of PageText objects, one per page
        """
        logger.info(f"Processing PDF: {pdf_path} with OCR mode: {self.ocr_mode}")
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if self.ocr_mode == OCRMode.OFF:
            return self._extract_text_only(pdf_path)
        elif self.ocr_mode == OCRMode.FORCE:
            return self._ocr_all_pages(pdf_path)
        else:  # AUTO mode
            return self._auto_process(pdf_path)
    
    def _extract_text_only(self, pdf_path: Path) -> List[PageText]:
        """Extract text without OCR."""
        logger.info("Extracting text without OCR")
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Create a single text block
                blocks = [TextBlock(text=text)] if text else []
                
                results.append(PageText(
                    page_number=page_num + 1,
                    text=text,
                    blocks=blocks,
                    ocr_applied=False,
                    source="text_extraction"
                ))
            
            doc.close()
            logger.info(f"Extracted text from {len(results)} pages without OCR")
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise
        
        return results
    
    def _auto_process(self, pdf_path: Path) -> List[PageText]:
        """
        Automatically decide whether to use OCR per page based on text content.
        """
        logger.info("Auto-processing PDF with selective OCR")
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                extracted_text = page.get_text()
                
                # Check if page has sufficient text
                is_low_text = len(extracted_text.strip()) < self.low_text_threshold
                
                if is_low_text:
                    logger.info(f"Page {page_num + 1} has low text content, applying OCR")
                    ocr_result = self._ocr_page(pdf_path, page_num)
                    if ocr_result:
                        # Merge extracted text with OCR text
                        merged_text = self._merge_texts(extracted_text, ocr_result.text)
                        results.append(PageText(
                            page_number=page_num + 1,
                            text=merged_text,
                            blocks=ocr_result.blocks,
                            ocr_applied=True,
                            source="hybrid"
                        ))
                    else:
                        # OCR failed, use extracted text
                        blocks = [TextBlock(text=extracted_text)] if extracted_text else []
                        results.append(PageText(
                            page_number=page_num + 1,
                            text=extracted_text,
                            blocks=blocks,
                            ocr_applied=False,
                            source="text_extraction"
                        ))
                else:
                    logger.debug(f"Page {page_num + 1} has sufficient text, skipping OCR")
                    blocks = [TextBlock(text=extracted_text)] if extracted_text else []
                    results.append(PageText(
                        page_number=page_num + 1,
                        text=extracted_text,
                        blocks=blocks,
                        ocr_applied=False,
                        source="text_extraction"
                    ))
            
            doc.close()
            logger.info(f"Auto-processed {len(results)} pages")
        except Exception as e:
            logger.error(f"Error in auto-processing: {e}")
            raise
        
        return results
    
    def _ocr_all_pages(self, pdf_path: Path) -> List[PageText]:
        """OCR all pages regardless of text content."""
        logger.info("Force OCR on all pages")
        results = []
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                ocr_result = self._ocr_page(pdf_path, page_num)
                if ocr_result:
                    results.append(ocr_result)
                else:
                    # OCR failed, fallback to text extraction
                    logger.warning(f"OCR failed for page {page_num + 1}, using text extraction")
                    page = doc[page_num]
                    extracted_text = page.get_text()
                    blocks = [TextBlock(text=extracted_text)] if extracted_text else []
                    results.append(PageText(
                        page_number=page_num + 1,
                        text=extracted_text,
                        blocks=blocks,
                        ocr_applied=False,
                        source="text_extraction"
                    ))
            
            doc.close()
            logger.info(f"OCR'd {len(results)} pages")
        except Exception as e:
            logger.error(f"Error in force OCR: {e}")
            raise
        
        return results
    
    def _ocr_page(self, pdf_path: Path, page_num: int) -> Optional[PageText]:
        """
        OCR a single page with retry logic.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Zero-indexed page number
            
        Returns:
            PageText object or None if OCR fails
        """
        for attempt in range(self.max_retries):
            try:
                # Render page to image
                image = self._render_page(pdf_path, page_num)
                if not image:
                    logger.error(f"Failed to render page {page_num + 1}")
                    return None
                
                # Perform OCR with detailed data
                ocr_data = pytesseract.image_to_data(
                    image,
                    output_type=pytesseract.Output.DICT,
                    config='--psm 3'  # Fully automatic page segmentation
                )
                
                # Extract text blocks with confidence and bbox
                blocks = []
                full_text_parts = []
                
                for i in range(len(ocr_data['text'])):
                    text = ocr_data['text'][i].strip()
                    if text:
                        conf = float(ocr_data['conf'][i])
                        if conf > 0:  # Valid confidence score
                            x0 = float(ocr_data['left'][i])
                            y0 = float(ocr_data['top'][i])
                            x1 = x0 + float(ocr_data['width'][i])
                            y1 = y0 + float(ocr_data['height'][i])
                            
                            blocks.append(TextBlock(
                                text=text,
                                bbox=(x0, y0, x1, y1),
                                confidence=conf
                            ))
                            full_text_parts.append(text)
                
                full_text = ' '.join(full_text_parts)
                
                logger.info(f"OCR completed for page {page_num + 1}, extracted {len(blocks)} text blocks")
                
                return PageText(
                    page_number=page_num + 1,
                    text=full_text,
                    blocks=blocks,
                    ocr_applied=True,
                    source="ocr"
                )
                
            except Exception as e:
                logger.warning(f"OCR attempt {attempt + 1}/{self.max_retries} failed for page {page_num + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"OCR failed for page {page_num + 1} after {self.max_retries} attempts")
                    return None
    
    def _render_page(self, pdf_path: Path, page_num: int) -> Optional[Image.Image]:
        """
        Render a PDF page to an image, trying PyMuPDF first, then pdf2image.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Zero-indexed page number
            
        Returns:
            PIL Image object or None if rendering fails
        """
        # Try PyMuPDF first (faster)
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            # Render at 300 DPI for good OCR quality
            mat = fitz.Matrix(300 / 72, 300 / 72)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            
            logger.debug(f"Rendered page {page_num + 1} using PyMuPDF")
            return img
            
        except Exception as e:
            logger.warning(f"PyMuPDF rendering failed for page {page_num + 1}: {e}, trying pdf2image")
            
            # Fallback to pdf2image
            try:
                images = convert_from_path(
                    pdf_path,
                    dpi=300,
                    first_page=page_num + 1,
                    last_page=page_num + 1
                )
                if images:
                    logger.debug(f"Rendered page {page_num + 1} using pdf2image")
                    return images[0]
                else:
                    logger.error(f"pdf2image returned no images for page {page_num + 1}")
                    return None
                    
            except Exception as e2:
                logger.error(f"pdf2image rendering failed for page {page_num + 1}: {e2}")
                return None
    
    def _merge_texts(self, extracted: str, ocr_text: str) -> str:
        """
        Merge text from extraction and OCR, preferring OCR if significantly longer.
        
        Args:
            extracted: Text from standard extraction
            ocr_text: Text from OCR
            
        Returns:
            Merged text
        """
        if not extracted.strip():
            return ocr_text
        if not ocr_text.strip():
            return extracted
        
        # If OCR text is significantly longer, prefer it
        if len(ocr_text) > len(extracted) * 1.5:
            logger.debug("Using OCR text (significantly longer)")
            return ocr_text
        
        # Otherwise combine both, removing duplicates
        combined = f"{extracted}\n\n[OCR Content]\n{ocr_text}"
        logger.debug("Merged extracted and OCR text")
        return combined
