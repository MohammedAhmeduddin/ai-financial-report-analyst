from pathlib import Path
from typing import List, Dict

class PDFParseError(Exception):
    pass


def extract_text_by_page(pdf_path: Path) -> List[Dict]:
    try:
        import pdfplumber
    except ImportError:
        raise PDFParseError("pdfplumber not installed")

    pages = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append({"page": i, "text": text.strip()})
    except Exception as e:
        raise PDFParseError(str(e))

    return pages
