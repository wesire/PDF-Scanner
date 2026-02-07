"""
Unit tests for PDF text extractor with pypdf and pdfplumber fallback.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

try:
    from src.pdf_text_extractor import PDFTextExtractor
except ImportError:
    # Fallback for running tests without installation
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.pdf_text_extractor import PDFTextExtractor


class TestPDFTextExtractor(unittest.TestCase):
    """Test cases for PDFTextExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = PDFTextExtractor(output_dir=self.temp_dir)

    def test_initialization(self):
        """Test extractor initialization."""
        self.assertTrue(Path(self.temp_dir).exists())
        self.assertEqual(self.extractor.output_dir, Path(self.temp_dir))

    @patch('src.pdf_text_extractor.pypdf')
    def test_extract_text_pypdf_success(self, mock_pypdf):
        """Test successful text extraction with pypdf."""
        # Mock PDF reader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text from pypdf"
        
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [mock_page]
        
        mock_pypdf.PdfReader.return_value = mock_reader
        
        # Test extraction
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_text_pypdf(tmp_path, 0)
        
        self.assertEqual(result, "Sample text from pypdf")
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pypdf')
    def test_extract_text_pypdf_encrypted(self, mock_pypdf):
        """Test pypdf handling of encrypted PDFs."""
        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_text_pypdf(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pypdf')
    def test_extract_text_pypdf_exception(self, mock_pypdf):
        """Test pypdf handling of exceptions."""
        mock_pypdf.PdfReader.side_effect = Exception("Corrupt PDF")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_text_pypdf(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pdfplumber')
    def test_extract_text_pdfplumber_success(self, mock_pdfplumber):
        """Test successful text extraction with pdfplumber."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text from pdfplumber"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.open.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_text_pdfplumber(tmp_path, 0)
        
        self.assertEqual(result, "Sample text from pdfplumber")
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pdfplumber')
    def test_extract_text_pdfplumber_exception(self, mock_pdfplumber):
        """Test pdfplumber handling of exceptions."""
        mock_pdfplumber.open.side_effect = Exception("Corrupt PDF")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_text_pdfplumber(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pdfplumber')
    @patch('src.pdf_text_extractor.pypdf')
    def test_extract_page_pypdf_success(self, mock_pypdf, mock_pdfplumber):
        """Test extract_page using pypdf successfully."""
        expected_text = "Test page text"
        mock_page = MagicMock()
        mock_page.extract_text.return_value = expected_text
        
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [mock_page]
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_page(tmp_path, 0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['page'], 0)
        self.assertEqual(result['chars'], len(expected_text))
        self.assertEqual(result['extraction_method'], 'pypdf')
        self.assertEqual(result['text'], expected_text)
        self.assertIn('file', result)
        
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pdfplumber')
    @patch('src.pdf_text_extractor.pypdf')
    def test_extract_page_fallback_to_pdfplumber(self, mock_pypdf, mock_pdfplumber):
        """Test extract_page falling back to pdfplumber when pypdf fails."""
        expected_text = "Fallback text"
        
        # pypdf fails
        mock_pypdf.PdfReader.side_effect = Exception("pypdf error")
        
        # pdfplumber succeeds
        mock_page = MagicMock()
        mock_page.extract_text.return_value = expected_text
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        mock_pdfplumber.open.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_page(tmp_path, 0)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['extraction_method'], 'pdfplumber')
        self.assertEqual(result['text'], expected_text)
        
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pdfplumber')
    @patch('src.pdf_text_extractor.pypdf')
    def test_extract_page_both_fail(self, mock_pypdf, mock_pdfplumber):
        """Test extract_page when both extractors fail."""
        mock_pypdf.PdfReader.side_effect = Exception("pypdf error")
        mock_pdfplumber.open.side_effect = Exception("pdfplumber error")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_page(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pypdf')
    def test_get_page_count_success(self, mock_pypdf):
        """Test getting page count from PDF."""
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [MagicMock(), MagicMock(), MagicMock()]
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.get_page_count(tmp_path)
        
        self.assertEqual(result, 3)
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pdfplumber')
    @patch('src.pdf_text_extractor.pypdf')
    def test_get_page_count_fallback(self, mock_pypdf, mock_pdfplumber):
        """Test getting page count with fallback to pdfplumber."""
        mock_pypdf.PdfReader.side_effect = Exception("pypdf error")
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock(), MagicMock()]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        mock_pdfplumber.open.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.get_page_count(tmp_path)
        
        self.assertEqual(result, 2)
        Path(tmp_path).unlink()

    @patch.object(PDFTextExtractor, 'extract_page')
    @patch.object(PDFTextExtractor, 'get_page_count')
    def test_extract_pdf_multiple_pages(self, mock_get_page_count, mock_extract_page):
        """Test extracting all pages from a PDF."""
        mock_get_page_count.return_value = 3
        
        mock_extract_page.side_effect = [
            {'page': 0, 'text': 'Page 0', 'chars': 6, 'extraction_method': 'pypdf'},
            {'page': 1, 'text': 'Page 1', 'chars': 6, 'extraction_method': 'pypdf'},
            {'page': 2, 'text': 'Page 2', 'chars': 6, 'extraction_method': 'pypdf'},
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            results = self.extractor.extract_pdf(tmp_path)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(mock_extract_page.call_count, 3)
        Path(tmp_path).unlink()

    @patch.object(PDFTextExtractor, 'extract_page')
    @patch.object(PDFTextExtractor, 'get_page_count')
    def test_extract_pdf_skip_failed_pages(self, mock_get_page_count, mock_extract_page):
        """Test that failed pages are skipped but processing continues."""
        mock_get_page_count.return_value = 3
        
        # Page 1 fails, but pages 0 and 2 succeed
        mock_extract_page.side_effect = [
            {'page': 0, 'text': 'Page 0', 'chars': 6, 'extraction_method': 'pypdf'},
            None,  # Page 1 fails
            {'page': 2, 'text': 'Page 2', 'chars': 6, 'extraction_method': 'pypdf'},
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            results = self.extractor.extract_pdf(tmp_path)
        
        # Only 2 pages should be returned (failed page skipped)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['page'], 0)
        self.assertEqual(results[1]['page'], 2)
        Path(tmp_path).unlink()

    def test_save_to_jsonl(self):
        """Test saving data to JSONL format."""
        test_data = [
            {'page': 0, 'text': 'Page 0', 'chars': 6, 'file': 'test.pdf', 'extraction_method': 'pypdf'},
            {'page': 1, 'text': 'Page 1', 'chars': 6, 'file': 'test.pdf', 'extraction_method': 'pypdf'},
        ]
        
        output_path = self.extractor.save_to_jsonl(test_data, 'test_output.jsonl')
        
        self.assertTrue(output_path.exists())
        
        # Read and verify JSONL content
        with open(output_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        
        # Verify each line is valid JSON
        for i, line in enumerate(lines):
            data = json.loads(line)
            self.assertEqual(data['page'], i)
            self.assertEqual(data['text'], f'Page {i}')

    @patch.object(PDFTextExtractor, 'extract_pdf')
    @patch.object(PDFTextExtractor, 'save_to_jsonl')
    def test_process_pdf(self, mock_save, mock_extract):
        """Test complete PDF processing workflow."""
        test_data = [
            {'page': 0, 'text': 'Page 0', 'chars': 6, 'file': 'test.pdf', 'extraction_method': 'pypdf'}
        ]
        mock_extract.return_value = test_data
        mock_save.return_value = Path(self.temp_dir) / 'test.jsonl'
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.process_pdf(tmp_path)
        
        mock_extract.assert_called_once()
        mock_save.assert_called_once()
        
        # Verify default filename
        call_args = mock_save.call_args
        self.assertTrue(call_args[0][1].endswith('.jsonl'))
        
        Path(tmp_path).unlink()

    def test_extract_pdf_file_not_found(self):
        """Test handling of non-existent PDF file."""
        result = self.extractor.extract_pdf('/nonexistent/file.pdf')
        self.assertEqual(result, [])

    @patch('src.pdf_text_extractor.pypdf', None)
    def test_extract_text_pypdf_not_installed(self):
        """Test behavior when pypdf is not installed."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_text_pypdf(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.pdf_text_extractor.pdfplumber', None)
    def test_extract_text_pdfplumber_not_installed(self):
        """Test behavior when pdfplumber is not installed."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = self.extractor.extract_text_pdfplumber(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()


if __name__ == '__main__':
    unittest.main()
