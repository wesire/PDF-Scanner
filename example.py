#!/usr/bin/env python3
"""
Example usage of PDF Text Extractor.

This script demonstrates how to use the PDFTextExtractor to extract text
from PDF files and save to JSONL format.
"""
import sys
from pathlib import Path

try:
    from src.pdf_text_extractor import PDFTextExtractor
except ImportError:
    # Fallback for development without installation
    sys.path.insert(0, str(Path(__file__).parent))
    from src.pdf_text_extractor import PDFTextExtractor


def main():
    """Main function."""
    # Initialize extractor
    extractor = PDFTextExtractor(output_dir="data/extracted")
    
    # Example: Process a PDF file
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    if pdf_path is None:
        print("Usage: python example.py <path_to_pdf>")
        print("\nThis will extract text from the PDF and save to data/extracted/")
        return 1
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1
    
    print(f"Processing PDF: {pdf_path}")
    print("-" * 60)
    
    # Process the PDF
    output_path = extractor.process_pdf(pdf_path)
    
    print(f"\nExtraction complete!")
    print(f"Output saved to: {output_path}")
    
    # Display summary
    import json
    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\nExtracted {len(lines)} pages")
    
    if lines:
        print("\nSample (first page):")
        first_page = json.loads(lines[0])
        print(f"  Page: {first_page['page']}")
        print(f"  Characters: {first_page['chars']}")
        print(f"  Extraction method: {first_page['extraction_method']}")
        print(f"  Text preview: {first_page['text'][:200]}...")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
