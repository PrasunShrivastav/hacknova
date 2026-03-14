"""PDF reader tool — lightweight abstract extraction fallback.

For ARIA's primary pipeline we work with abstracts (from APIs),
but this tool can fetch and extract text from arXiv PDF URLs
when deeper full-text analysis is needed.
"""

import httpx
import io
import logging

logger = logging.getLogger(__name__)


def fetch_pdf_text(pdf_url: str, max_pages: int = 5) -> str:
    """Download a PDF and extract text from first N pages.

    Uses a lightweight approach: try to read the PDF as bytes and
    extract text. Falls back gracefully if PyPDF is unavailable.

    Args:
        pdf_url: URL to the PDF file.
        max_pages: Maximum pages to extract (default 5).

    Returns:
        Extracted text string, or empty string on failure.
    """
    logger.info(f"Fetching PDF from: {pdf_url}")
    try:
        resp = httpx.get(pdf_url, timeout=60, follow_redirects=True)
        resp.raise_for_status()
        pdf_bytes = resp.content
    except Exception as e:
        logger.error(f"PDF download failed: {e}")
        return ""

    # Try PyPDF2 (pypdf) for text extraction
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for i, page in enumerate(reader.pages[:max_pages]):
            text_parts.append(page.extract_text() or "")
        text = "\n\n".join(text_parts)
        logger.info(f"Extracted {len(text)} chars from {min(max_pages, len(reader.pages))} pages")
        return text
    except ImportError:
        logger.warning("pypdf not installed — PDF text extraction unavailable. Install with: pip install pypdf")
        return ""
    except Exception as e:
        logger.error(f"PDF text extraction error: {e}")
        return ""


def extract_sections(text: str) -> dict[str, str]:
    """Attempt to split extracted PDF text into common paper sections.

    Args:
        text: Raw extracted text from a PDF.

    Returns:
        Dict mapping section names to content.
    """
    sections: dict[str, str] = {"full_text": text}
    section_markers = [
        "abstract", "introduction", "related work", "background",
        "method", "methodology", "approach", "experiment",
        "results", "discussion", "conclusion", "references",
    ]

    text_lower = text.lower()
    positions = []
    for marker in section_markers:
        idx = text_lower.find(marker)
        if idx != -1:
            positions.append((idx, marker))

    positions.sort(key=lambda x: x[0])

    for i, (pos, name) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        sections[name] = text[pos:end].strip()

    return sections
