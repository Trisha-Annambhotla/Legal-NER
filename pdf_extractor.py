"""
pdf_extractor.py
----------------
Extracts text from Indian High Court judgment PDFs using pdfplumber.
Handles multi-page PDFs and returns per-page text for downstream processing.
"""

import pdfplumber
import os
from typing import List, Dict


def extract_text_from_pdf(pdf_path: str) -> Dict:
    """
    Extract text from a PDF file page by page.

    Args:
        pdf_path: Full path to the PDF file.

    Returns:
        A dict with:
            - 'pages': list of dicts, each with 'page_num' and 'text'
            - 'full_text': concatenated text of all pages
            - 'total_pages': number of pages
            - 'filename': base name of the PDF
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at path: {pdf_path}")

    pages_data: List[Dict] = []
    full_text_parts: List[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages, start=1):
            # Extract raw text; returns None if page has no text layer
            raw_text = page.extract_text()

            if raw_text:
                pages_data.append({
                    "page_num": page_num,
                    "text": raw_text
                })
                full_text_parts.append(raw_text)
            else:
                # Scanned/image-based page — flag it but don't crash
                pages_data.append({
                    "page_num": page_num,
                    "text": "",
                    "warning": "No text layer found (possibly scanned image)"
                })

    full_text = "\n\n".join(full_text_parts)

    return {
        "filename": os.path.basename(pdf_path),
        "total_pages": total_pages,
        "pages": pages_data,
        "full_text": full_text
    }


def extract_from_directory(directory: str, extension: str = ".pdf") -> List[Dict]:
    """
    Batch-extract text from all PDFs in a directory.

    Args:
        directory: Path to folder containing PDF files.
        extension: File extension to filter (default '.pdf').

    Returns:
        List of extraction results, one per PDF file.
    """
    results = []
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Not a directory: {directory}")

    pdf_files = [
        f for f in os.listdir(directory)
        if f.lower().endswith(extension)
    ]

    if not pdf_files:
        print(f"[WARNING] No PDF files found in: {directory}")
        return results

    for filename in sorted(pdf_files):
        full_path = os.path.join(directory, filename)
        print(f"[INFO] Extracting: {filename}")
        try:
            result = extract_text_from_pdf(full_path)
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Failed to extract {filename}: {e}")

    return results


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    test_path = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"
    data = extract_text_from_pdf(test_path)
    print(f"File     : {data['filename']}")
    print(f"Pages    : {data['total_pages']}")
    print(f"Preview  :\n{data['full_text'][:500]}")
