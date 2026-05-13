"""
Document loaders for permit and reference documents.

Takes a file on disk, returns a list of (text, page_number) tuples.
Phase 2 fills in the actual parsing.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_pdf(path):
    """Load a PDF and return a list of (page_text, page_number) tuples.

    TODO: implement using pdfplumber.
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return [(page.extract_text() or "", i + 1)
                    for i, page in enumerate(pdf.pages)]
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF: {path}")

    logger.warning("load_pdf not yet implemented")
    return []


def load_docx(path):
    """Load a DOCX and return a list of (paragraph_text, page_number) tuples.

    Note: DOCX doesn't have native page numbers — they're approximated.

    TODO: implement using python-docx.
        from docx import Document
        doc = Document(path)
        # walk paragraphs, track page breaks
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX not found: {path}")
    if path.suffix.lower() != ".docx":
        raise ValueError(f"Not a DOCX: {path}")

    logger.warning("load_docx not yet implemented")
    return []


def load_document(path):
    """Dispatch to the right loader based on file extension."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix == ".docx":
        return load_docx(path)
    raise ValueError(f"Unsupported file type: {suffix}")
