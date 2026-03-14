"""arXiv search tool — completely free, no API key needed."""

import arxiv
import time
import logging

logger = logging.getLogger(__name__)


def search_arxiv(query: str, max_results: int = 20) -> list[dict]:
    """Search arXiv for papers matching the query.

    Args:
        query: Natural language or keyword search query.
        max_results: Maximum papers to return (default 20).

    Returns:
        List of paper dicts with title, abstract, authors, year, url, etc.
    """
    logger.info(f"Searching arXiv for: '{query}' (max {max_results})")
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []
    try:
        for result in client.results(search):
            papers.append({
                "title": result.title,
                "abstract": result.summary,
                "authors": [a.name for a in result.authors],
                "year": result.published.year if result.published else None,
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "source": "arxiv",
                "arxiv_id": result.entry_id.split("/")[-1],
                "paper_id": result.entry_id.split("/")[-1],
            })
            time.sleep(0.5)  # Be polite to arXiv
    except Exception as e:
        logger.error(f"arXiv search error: {e}")

    logger.info(f"arXiv returned {len(papers)} papers")
    return papers
