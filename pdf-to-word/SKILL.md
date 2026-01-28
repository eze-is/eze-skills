---
name: pdf-to-word
description: PDF to Word document converter. Converts PDF files to editable Word (.docx) documents while preserving formatting, tables, and images. Use when user asks to convert PDF to Word, transform PDF to DOCX, create editable Word document from PDF, or export PDF as Word format.
---

# PDF to Word Converter

## Overview

This skill converts PDF files into editable Word (.docx) documents using the `pdf2docx` library. It preserves document formatting including text, tables, images, and layout.

## Quick Start

```bash
# Basic conversion (output file auto-named)
python3 scripts/convert.py input.pdf

# Specify output file
python3 scripts/convert.py input.pdf -o output.docx
```

## Requirements

The script requires `pdf2docx` library. Install it first:

```bash
pip install pdf2docx
```

**Note:** On externally-managed Python environments (macOS with Homebrew Python), you may need:
```bash
pip install --break-system-packages pdf2docx
```

## Usage

### Direct Script Execution

The most reliable method is to run the conversion script directly:

```bash
python3 /path/to/skill/scripts/convert.py <pdf_file> [-o output.docx]
```

### Workflow

1. **Identify input PDF** - Get the absolute path to the PDF file
2. **Determine output path** - Default: same directory as PDF with .docx extension
3. **Run conversion** - Execute the script with appropriate arguments
4. **Verify output** - Confirm the Word document was created successfully

## Limitations

- Best results with text-based PDFs (not scanned images)
- Complex layouts may require manual adjustments
- Password-protected PDFs must be unlocked first
- Very large files may take time to process

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: pdf2docx` | Install: `pip install pdf2docx` |
| `PDF file not found` | Use absolute path to the PDF file |
| Poor formatting | Manual cleanup may be needed for complex PDFs |
