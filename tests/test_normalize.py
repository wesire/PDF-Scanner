"""
Unit tests for text normalization module.
"""
import sys
import unittest
from pathlib import Path

try:
    from src.normalize import normalize_text, preserve_part_numbers, validate_part_number
except ImportError:
    # Fallback for running tests without installation
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.normalize import normalize_text, preserve_part_numbers, validate_part_number


class TestNormalize(unittest.TestCase):
    """Test cases for text normalization functions."""

    def test_normalize_text_none_input(self):
        """Test that None input returns empty string."""
        result = normalize_text(None)
        self.assertEqual(result, "")

    def test_normalize_text_empty_input(self):
        """Test that empty string input returns empty string."""
        result = normalize_text("")
        self.assertEqual(result, "")
        
        result = normalize_text("   ")
        self.assertEqual(result, "")

    def test_normalize_text_ligature_fixes(self):
        """Test that common OCR ligatures are fixed."""
        # Test fi ligature
        text = "The file contains information about ﬁnancial ﬁgures."
        result = normalize_text(text)
        self.assertEqual(result, "The file contains information about financial figures.")
        
        # Test fl ligature
        text = "The ﬂow of ﬂuid through the ﬂange."
        result = normalize_text(text)
        self.assertEqual(result, "The flow of fluid through the flange.")
        
        # Test ff ligature
        text = "The staﬀ had diﬀerent opinions."
        result = normalize_text(text)
        self.assertEqual(result, "The staff had different opinions.")
        
        # Test ffi ligature
        text = "The traﬃc was eﬃcient and suﬃcient."
        result = normalize_text(text)
        self.assertEqual(result, "The traffic was efficient and sufficient.")
        
        # Test ffl ligature
        text = "The baﬄed audience watched the shuﬄe."
        result = normalize_text(text)
        self.assertEqual(result, "The baffled audience watched the shuffle.")

    def test_normalize_text_apostrophe_fixes(self):
        """Test that common OCR apostrophe errors are fixed."""
        # Test various quote marks
        text = "It's the user's choice, don't worry."
        result = normalize_text(text)
        self.assertEqual(result, "It's the user's choice, don't worry.")
        
        # Test prime and grave accent
        text = "The item′s value and user`s data."
        result = normalize_text(text)
        self.assertEqual(result, "The item's value and user's data.")
        
        # Test acute accent
        text = "The company´s product line."
        result = normalize_text(text)
        self.assertEqual(result, "The company's product line.")

    def test_normalize_text_preserves_part_numbers(self):
        """Test that part numbers in format #K-####-# are preserved."""
        text = "Order part #K-1234-5 and part #K-9876-3 today."
        result = normalize_text(text)
        self.assertIn("#K-1234-5", result)
        self.assertIn("#K-9876-3", result)

    def test_normalize_text_line_boundaries(self):
        """Test that line-item boundaries are preserved."""
        text = "Line 1: Item A\nLine 2: Item B\nLine 3: Item C"
        result = normalize_text(text)
        lines = result.split('\n')
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0], "Line 1: Item A")
        self.assertEqual(lines[1], "Line 2: Item B")
        self.assertEqual(lines[2], "Line 3: Item C")

    def test_normalize_text_whitespace_normalization(self):
        """Test that excessive whitespace is normalized."""
        # Multiple spaces
        text = "This  has    multiple     spaces"
        result = normalize_text(text)
        self.assertEqual(result, "This has multiple spaces")
        
        # Tabs
        text = "This\thas\t\ttabs"
        result = normalize_text(text)
        self.assertEqual(result, "This has tabs")
        
        # Leading/trailing whitespace
        text = "  \t  Text with padding  \t  "
        result = normalize_text(text)
        self.assertEqual(result, "Text with padding")

    def test_normalize_text_multiple_blank_lines(self):
        """Test that multiple blank lines are reduced to double newline."""
        text = "Paragraph 1\n\n\n\nParagraph 2"
        result = normalize_text(text)
        self.assertEqual(result, "Paragraph 1\n\nParagraph 2")

    def test_normalize_text_line_endings(self):
        """Test that different line endings are normalized."""
        # Windows line endings
        text = "Line 1\r\nLine 2\r\nLine 3"
        result = normalize_text(text)
        self.assertEqual(result, "Line 1\nLine 2\nLine 3")
        
        # Old Mac line endings
        text = "Line 1\rLine 2\rLine 3"
        result = normalize_text(text)
        self.assertEqual(result, "Line 1\nLine 2\nLine 3")

    def test_normalize_text_comprehensive_example(self):
        """Test normalization with multiple issues in one text."""
        text = """The  manufacturer's  warranty  covers  ﬁnancial  losses.
        
        
Part #K-1234-5 - High-efﬁciency pump
Part #K-5678-9 - Flow  control  valve

It's designed for industrial  applications."""
        
        result = normalize_text(text)
        
        # Check ligatures are fixed
        self.assertIn("financial", result)
        self.assertIn("High-efficiency", result)
        
        # Check apostrophes are fixed
        self.assertIn("manufacturer's", result)
        self.assertIn("It's", result)
        
        # Check part numbers are preserved
        self.assertIn("#K-1234-5", result)
        self.assertIn("#K-5678-9", result)
        
        # Check whitespace is normalized
        self.assertNotIn("  ", result)
        
        # Check structure is maintained
        lines = result.split('\n')
        self.assertGreater(len(lines), 1)

    def test_preserve_part_numbers_single(self):
        """Test extracting a single part number."""
        text = "Order part #K-1234-5 today."
        result = preserve_part_numbers(text)
        self.assertEqual(result, ["#K-1234-5"])

    def test_preserve_part_numbers_multiple(self):
        """Test extracting multiple part numbers."""
        text = "Order #K-1234-5, #K-9876-3, and #K-5555-1."
        result = preserve_part_numbers(text)
        self.assertEqual(len(result), 3)
        self.assertIn("#K-1234-5", result)
        self.assertIn("#K-9876-3", result)
        self.assertIn("#K-5555-1", result)

    def test_preserve_part_numbers_none_found(self):
        """Test when no part numbers are in text."""
        text = "This text has no part numbers."
        result = preserve_part_numbers(text)
        self.assertEqual(result, [])

    def test_preserve_part_numbers_invalid_formats(self):
        """Test that invalid formats are not matched."""
        text = "#K-123-4 #K-12345-6 K-1234-5 #K-1234-56 #A-1234-5"
        result = preserve_part_numbers(text)
        self.assertEqual(result, [])

    def test_preserve_part_numbers_with_surrounding_text(self):
        """Test part numbers in various contexts."""
        text = """
        Part#K-1234-5 (no space)
        Part #K-5678-9 (with space)
        #K-9999-0, and more text
        """
        result = preserve_part_numbers(text)
        self.assertEqual(len(result), 3)
        self.assertIn("#K-1234-5", result)
        self.assertIn("#K-5678-9", result)
        self.assertIn("#K-9999-0", result)

    def test_validate_part_number_valid(self):
        """Test validation of valid part numbers."""
        self.assertTrue(validate_part_number("#K-1234-5"))
        self.assertTrue(validate_part_number("#K-0000-0"))
        self.assertTrue(validate_part_number("#K-9999-9"))

    def test_validate_part_number_invalid(self):
        """Test validation of invalid part numbers."""
        # Wrong prefix
        self.assertFalse(validate_part_number("#A-1234-5"))
        self.assertFalse(validate_part_number("K-1234-5"))
        
        # Wrong number of digits
        self.assertFalse(validate_part_number("#K-123-5"))
        self.assertFalse(validate_part_number("#K-12345-5"))
        self.assertFalse(validate_part_number("#K-1234-56"))
        
        # Missing parts
        self.assertFalse(validate_part_number("#K-1234"))
        self.assertFalse(validate_part_number("#K-1234-"))
        
        # Extra characters
        self.assertFalse(validate_part_number("#K-1234-5 "))
        self.assertFalse(validate_part_number(" #K-1234-5"))
        self.assertFalse(validate_part_number("#K-1234-5a"))

    def test_normalize_text_with_fixture(self):
        """Test normalization with fixture file."""
        fixture_path = Path(__file__).parent / "fixtures" / "parts_invoice.txt"
        
        if fixture_path.exists():
            with open(fixture_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            result = normalize_text(text)
            
            # Check part numbers are preserved
            part_numbers = preserve_part_numbers(result)
            self.assertGreater(len(part_numbers), 0)
            self.assertIn("#K-1234-5", part_numbers)
            self.assertIn("#K-5678-9", part_numbers)
            
            # Check ligatures are fixed
            self.assertNotIn("ﬁ", result)
            self.assertNotIn("ﬂ", result)
            self.assertIn("effi", result)  # Should be "efficiency"
            self.assertIn("flow", result)
            
            # Check apostrophes are normalized
            self.assertIn("manufacturer's", result)
            self.assertIn("It's", result)
            
            # Check line structure is maintained
            lines = result.split('\n')
            self.assertGreater(len(lines), 10)


if __name__ == '__main__':
    unittest.main()
