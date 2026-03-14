"""PDF text extractor — downloads and extracts text from paper PDFs."""

import httpx
import io
import logging
import time
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=3)


def extract_pdf_text(pdf_url: str, max_pages: int = 3) -> str:
    """Download a PDF and extract text from the first few pages.

    Args:
        pdf_url: URL to the PDF file.
        max_pages: Maximum pages to extract (default 3 — intro + methods).

    Returns:
        Extracted text string, or empty string on failure.
    """
    if not pdf_url:
        return ""

    try:
        response = httpx.get(pdf_url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()

        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(response.content))

        text_parts = []
        for i, page in enumerate(reader.pages[:max_pages]):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts)
        logger.info(f"Extracted {len(full_text)} chars from PDF ({min(len(reader.pages), max_pages)} pages)")
        return full_text[:8000]  # Cap to avoid huge payloads
    except ImportError:
        logger.warning("pypdf not installed — run: pip install pypdf")
        return ""
    except Exception as e:
        logger.warning(f"PDF extraction failed for {pdf_url[:60]}: {e}")
        return ""


def enrich_papers_with_pdf(papers: list[dict]) -> list[dict]:
    """Enrich papers that have pdf_url by extracting full text.

    Only processes papers with a pdf_url and a short abstract (<200 chars).
    Uses ThreadPoolExecutor for parallel downloads.

    Args:
        papers: List of paper dicts.

    Returns:
        Papers with 'full_text' field added where available.
    """
    papers_to_enrich = [
        (i, p) for i, p in enumerate(papers)
        if p.get("pdf_url") and p.get("source") == "arxiv"
    ]

    if not papers_to_enrich:
        logger.info("No papers with PDF URLs to enrich")
        return papers

    logger.info(f"Enriching {len(papers_to_enrich)} papers with PDF text...")

    def fetch_one(idx_paper):
        idx, paper = idx_paper
        text = extract_pdf_text(paper["pdf_url"], max_pages=3)
        return idx, text

    # Use the global executor directly without a 'with' block to avoid shutting it down
    results = list(_executor.map(fetch_one, papers_to_enrich))

    enriched_count = 0
    for idx, text in results:
        if text and len(text) > 100:
            papers[idx]["full_text"] = text
            # If abstract was empty/short, use the first 500 chars of PDF as abstract
            if not papers[idx].get("abstract") or len(papers[idx]["abstract"]) < 50:
                papers[idx]["abstract"] = text[:500].strip()
            enriched_count += 1

    logger.info(f"Enriched {enriched_count}/{len(papers_to_enrich)} papers with PDF text")
    return papers
