#!/usr/bin/env python3
"""
PDF to Word Converter

This script converts a PDF file to a Word (.docx) document.
Requires the pdf2docx library: pip install pdf2docx
"""

import sys
import argparse
from pathlib import Path


def convert_pdf_to_word(pdf_path: str, output_path: str = None) -> str:
    """
    Convert a PDF file to a Word (.docx) document.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Path to the output Word file (optional, defaults to PDF filename with .docx extension)

    Returns:
        Path to the created Word file
    """
    try:
        from pdf2docx import Converter
    except ImportError:
        print("Error: pdf2docx library is not installed.")
        print("Please install it using: pip install pdf2docx")
        sys.exit(1)

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    if output_path is None:
        output_path = pdf_file.with_suffix('.docx')
    else:
        output_path = Path(output_path)

    print(f"Converting {pdf_file} to {output_path}...")

    cv = Converter(str(pdf_file))
    cv.convert(str(output_path))
    cv.close()

    print(f"Successfully converted to: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Word (.docx) documents"
    )
    parser.add_argument(
        "pdf_file",
        help="Path to the input PDF file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to the output Word file (optional)",
        default=None
    )

    args = parser.parse_args()

    convert_pdf_to_word(args.pdf_file, args.output)


if __name__ == "__main__":
    main()
