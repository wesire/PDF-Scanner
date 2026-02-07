#!/usr/bin/env python3
"""
Demo script showing the normalize_text() function in action.

This script demonstrates the text normalization capabilities including:
- Preserving part numbers (#K-####-#)
- Fixing OCR ligature issues
- Fixing OCR apostrophe issues
- Maintaining line boundaries
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from normalize import normalize_text, preserve_part_numbers


def demo_normalize():
    """Demonstrate the normalize_text function."""
    
    print("=" * 70)
    print("Text Normalization Demo")
    print("=" * 70)
    print()
    
    # Example 1: OCR ligature issues
    print("Example 1: Fixing OCR Ligatures")
    print("-" * 70)
    text1 = "High-efﬁciency ﬂow controller for ﬁnancial systems."
    print(f"Before: {text1}")
    normalized1 = normalize_text(text1)
    print(f"After:  {normalized1}")
    print()
    
    # Example 2: OCR apostrophe issues
    print("Example 2: Fixing OCR Apostrophes")
    print("-" * 70)
    text2 = "The manufacturer's warranty doesn′t cover user`s errors."
    print(f"Before: {text2}")
    normalized2 = normalize_text(text2)
    print(f"After:  {normalized2}")
    print()
    
    # Example 3: Preserving part numbers
    print("Example 3: Preserving Part Numbers")
    print("-" * 70)
    text3 = "Order parts #K-1234-5 and #K-9876-3 today."
    print(f"Before: {text3}")
    normalized3 = normalize_text(text3)
    print(f"After:  {normalized3}")
    part_numbers = preserve_part_numbers(normalized3)
    print(f"Found part numbers: {part_numbers}")
    print()
    
    # Example 4: Complex text with multiple issues
    print("Example 4: Complex Example with Multiple Issues")
    print("-" * 70)
    text4 = """Part #K-5678-9 - High-efﬁciency Pump
Price: $1,250.00
The manufacturer's warranty covers ﬁnancial losses.
It's  designed  for   industrial   applications."""
    
    print("Before:")
    print(text4)
    normalized4 = normalize_text(text4)
    print("\nAfter:")
    print(normalized4)
    part_numbers = preserve_part_numbers(normalized4)
    print(f"\nFound part numbers: {part_numbers}")
    print()
    
    # Example 5: Using fixture file
    print("Example 5: Processing Fixture File")
    print("-" * 70)
    fixture_path = Path(__file__).parent / "tests" / "fixtures" / "parts_invoice.txt"
    if fixture_path.exists():
        with open(fixture_path, 'r', encoding='utf-8') as f:
            text5 = f.read()
        
        print(f"File: {fixture_path.name}")
        print(f"Original length: {len(text5)} characters")
        
        normalized5 = normalize_text(text5)
        print(f"Normalized length: {len(normalized5)} characters")
        
        part_numbers = preserve_part_numbers(normalized5)
        print(f"Found {len(part_numbers)} part numbers:")
        for pn in part_numbers:
            print(f"  - {pn}")
        
        # Show a sample of before/after
        print("\nSample from original:")
        print(text5[400:550])
        print("\nSame section after normalization:")
        print(normalized5[400:550])
    else:
        print(f"Fixture file not found: {fixture_path}")
    
    print()
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo_normalize()
