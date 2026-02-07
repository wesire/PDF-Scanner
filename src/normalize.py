"""
Text normalization for OCR-extracted content.

This module provides functions for normalizing text extracted from PDFs,
including fixing common OCR errors while preserving important patterns
like part numbers and line-item boundaries.
"""
import re
from typing import Optional


def normalize_text(text: Optional[str]) -> str:
    """
    Normalize OCR-extracted text while preserving structure and part numbers.
    
    This function:
    - Preserves part numbers matching pattern #K-####-# (e.g., #K-1234-5)
    - Fixes common OCR apostrophe issues (various quote marks → standard apostrophe)
    - Fixes common OCR ligature issues (ﬁ → fi, ﬂ → fl, ﬀ → ff, ﬃ → ffi, ﬄ → ffl)
    - Keeps line-item boundaries intact (preserves newlines)
    - Normalizes whitespace while maintaining paragraph structure
    
    Args:
        text: The text to normalize (can be None)
        
    Returns:
        Normalized text string (empty string if input is None)
    """
    if text is None:
        return ""
    
    # Return empty string for empty input
    if not text.strip():
        return ""
    
    # Fix common OCR ligature issues
    # These are often misread by OCR and need to be converted to standard characters
    ligature_map = {
        'ﬁ': 'fi',  # Latin small ligature fi
        'ﬂ': 'fl',  # Latin small ligature fl
        'ﬀ': 'ff',  # Latin small ligature ff
        'ﬃ': 'ffi', # Latin small ligature ffi
        'ﬄ': 'ffl', # Latin small ligature ffl
        'ﬅ': 'st',  # Latin small ligature st
        'ﬆ': 'st',  # Latin small ligature st (alternate)
    }
    
    for ligature, replacement in ligature_map.items():
        text = text.replace(ligature, replacement)
    
    # Fix common OCR apostrophe and quote issues
    # OCR often misreads apostrophes as various quote marks
    apostrophe_map = {
        ''': "'",  # Right single quotation mark
        ''': "'",  # Left single quotation mark
        '‛': "'",  # Single high-reversed-9 quotation mark
        '′': "'",  # Prime (often confused with apostrophe)
        '`': "'",  # Grave accent (often confused with apostrophe)
        '´': "'",  # Acute accent (often confused with apostrophe)
    }
    
    for wrong_char, correct_char in apostrophe_map.items():
        text = text.replace(wrong_char, correct_char)
    
    # Normalize line endings to \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove multiple consecutive blank lines but keep single line breaks
    # This preserves line-item boundaries
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Normalize horizontal whitespace on each line but preserve line structure
    lines = text.split('\n')
    normalized_lines = []
    
    for line in lines:
        # Replace multiple spaces/tabs with single space
        normalized_line = re.sub(r'[ \t]+', ' ', line)
        # Strip leading/trailing whitespace from each line
        normalized_line = normalized_line.strip()
        normalized_lines.append(normalized_line)
    
    # Rejoin with newlines to preserve line structure
    text = '\n'.join(normalized_lines)
    
    # Remove leading/trailing blank lines
    text = text.strip()
    
    return text


def preserve_part_numbers(text: str) -> list[str]:
    """
    Extract part numbers from text that match the pattern #K-####-#.
    
    Pattern explanation:
    - Starts with #K-
    - Followed by 4 digits
    - Followed by -
    - Ends with a single digit
    
    Example matches: #K-1234-5, #K-9876-1
    
    Args:
        text: Text to search for part numbers
        
    Returns:
        List of part numbers found in the text
    """
    # Pattern for part numbers: #K-####-#
    # Use word boundary \b at the end to ensure we don't match longer numbers
    pattern = r'#K-\d{4}-\d\b'
    return re.findall(pattern, text)


def validate_part_number(part_number: str) -> bool:
    """
    Validate if a string matches the part number pattern #K-####-#.
    
    Args:
        part_number: String to validate
        
    Returns:
        True if the string is a valid part number, False otherwise
    """
    pattern = r'^#K-\d{4}-\d$'
    return bool(re.match(pattern, part_number))
