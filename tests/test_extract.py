"""
Unit tests for text extraction module.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

try:
    from src.extract import extract_text, extract_text_pdfplumber, extract_text_pypdf
except ImportError:
    # Fallback for running tests without installation
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.extract import extract_text, extract_text_pdfplumber, extract_text_pypdf


class TestExtract(unittest.TestCase):
    """Test cases for text extraction functions."""

    @patch('src.extract.pypdf')
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
            result = extract_text_pypdf(tmp_path, 0)
        
        self.assertEqual(result, "Sample text from pypdf")
        Path(tmp_path).unlink()

    @patch('src.extract.pypdf')
    def test_extract_text_pypdf_encrypted(self, mock_pypdf):
        """Test pypdf handling of encrypted PDFs."""
        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = extract_text_pypdf(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.extract.pypdf')
    def test_extract_text_pypdf_exception(self, mock_pypdf):
        """Test pypdf handling of exceptions."""
        mock_pypdf.PdfReader.side_effect = Exception("Corrupt PDF")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = extract_text_pypdf(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.extract.pypdf')
    def test_extract_text_pypdf_empty_text(self, mock_pypdf):
        """Test pypdf when page has no text."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [mock_page]
        
        mock_pypdf.PdfReader.return_value = mock_reader
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = extract_text_pypdf(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.extract.pdfplumber')
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
            result = extract_text_pdfplumber(tmp_path, 0)
        
        self.assertEqual(result, "Sample text from pdfplumber")
        Path(tmp_path).unlink()

    @patch('src.extract.pdfplumber')
    def test_extract_text_pdfplumber_exception(self, mock_pdfplumber):
        """Test pdfplumber handling of exceptions."""
        mock_pdfplumber.open.side_effect = Exception("Corrupt PDF")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = extract_text_pdfplumber(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.extract.pdfplumber')
    def test_extract_text_pdfplumber_empty_text(self, mock_pdfplumber):
        """Test pdfplumber when page has no text."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        
        mock_pdfplumber.open.return_value = mock_pdf
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = extract_text_pdfplumber(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.extract.extract_text_pdfplumber')
    @patch('src.extract.extract_text_pypdf')
    def test_extract_text_uses_pypdf_first(self, mock_pypdf_extract, mock_pdfplumber_extract):
        """Test extract_text using pypdf successfully."""
        mock_pypdf_extract.return_value = "Text from pypdf"
        
        text, method = extract_text("test.pdf", 0)
        
        self.assertEqual(text, "Text from pypdf")
        self.assertEqual(method, "pypdf")
        mock_pypdf_extract.assert_called_once_with("test.pdf", 0)
        mock_pdfplumber_extract.assert_not_called()

    @patch('src.extract.extract_text_pdfplumber')
    @patch('src.extract.extract_text_pypdf')
    def test_extract_text_fallback_to_pdfplumber(self, mock_pypdf_extract, mock_pdfplumber_extract):
        """Test extract_text falling back to pdfplumber when pypdf fails."""
        mock_pypdf_extract.return_value = None
        mock_pdfplumber_extract.return_value = "Text from pdfplumber"
        
        text, method = extract_text("test.pdf", 0)
        
        self.assertEqual(text, "Text from pdfplumber")
        self.assertEqual(method, "pdfplumber")
        mock_pypdf_extract.assert_called_once_with("test.pdf", 0)
        mock_pdfplumber_extract.assert_called_once_with("test.pdf", 0)

    @patch('src.extract.extract_text_pdfplumber')
    @patch('src.extract.extract_text_pypdf')
    def test_extract_text_both_fail(self, mock_pypdf_extract, mock_pdfplumber_extract):
        """Test extract_text when both extractors fail."""
        mock_pypdf_extract.return_value = None
        mock_pdfplumber_extract.return_value = None
        
        text, method = extract_text("test.pdf", 0)
        
        self.assertIsNone(text)
        self.assertEqual(method, "none")
        mock_pypdf_extract.assert_called_once()
        mock_pdfplumber_extract.assert_called_once()

    @patch('src.extract.pypdf', None)
    def test_extract_text_pypdf_not_installed(self):
        """Test behavior when pypdf is not installed."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = extract_text_pypdf(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()

    @patch('src.extract.pdfplumber', None)
    def test_extract_text_pdfplumber_not_installed(self):
        """Test behavior when pdfplumber is not installed."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            result = extract_text_pdfplumber(tmp_path, 0)
        
        self.assertIsNone(result)
        Path(tmp_path).unlink()


if __name__ == '__main__':
    unittest.main()
