"""Semantic Scholar search tool — free tier, no API key needed for basic search."""

import httpx
import time
import logging

logger = logging.getLogger(__name__)

BASE = "https://api.semanticscholar.org/graph/v1"


def search_semantic_scholar(query: str, max_results: int = 20) -> list[dict]:
    """Search Semantic Scholar for papers matching the query.

    Uses the public endpoint (no API key) — rate limited to ~100 req / 5 min.

    Args:
        query: Search query string.
        max_results: Maximum papers to return.

    Returns:
        List of paper dicts with title, abstract, authors, year, etc.
    """
    logger.info(f"Searching Semantic Scholar for: '{query}' (max {max_results})")
    params = {
        "query": query,
        "limit": min(max_results, 100),
        "fields": "title,abstract,year,authors,citationCount,externalIds,url",
    }

    papers = []
    for attempt in range(3):
        try:
            resp = httpx.get(f"{BASE}/paper/search", params=params, timeout=30)
            if resp.status_code == 429:
                wait = (attempt + 1) * 5
                logger.warning(f"Semantic Scholar rate limit (attempt {attempt+1}), waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json().get("data") or []

            for p in data:
                external_ids = p.get("externalIds") or {}
                papers.append({
                    "title": p.get("title", ""),
                    "abstract": p.get("abstract", "") or "",
                    "authors": [a["name"] for a in p.get("authors", []) if "name" in a],
                    "year": p.get("year"),
                    "citation_count": p.get("citationCount", 0),
                    "paper_id": p.get("paperId", ""),
                    "arxiv_id": external_ids.get("ArXiv", ""),
                    "url": p.get("url", ""),
                    "source": "semantic_scholar",
                })
            break  # Success, stop retrying
        except httpx.HTTPStatusError as e:
            logger.error(f"Semantic Scholar HTTP error: {e}")
            break
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            break

    logger.info(f"Semantic Scholar returned {len(papers)} papers")
    return papers


def get_citations(paper_id: str) -> list[dict]:
    """Get references (citation trail) for a given paper — no key needed.

    Args:
        paper_id: Semantic Scholar paper ID.

    Returns:
        List of referenced paper dicts (up to 10).
    """
    logger.info(f"Fetching citations for paper: {paper_id}")
    try:
        resp = httpx.get(
            f"{BASE}/paper/{paper_id}/references",
            params={"fields": "title,abstract,year,authors,citationCount,externalIds", "limit": 10},
            timeout=30,
        )
        if resp.status_code == 429:
            logger.warning("Rate limited on citations. Waiting 30s...")
            time.sleep(30)
            resp = httpx.get(
                f"{BASE}/paper/{paper_id}/references",
                params={"fields": "title,abstract,year,authors,citationCount,externalIds", "limit": 10},
                timeout=30,
            )
        if resp.status_code != 200:
            logger.warning(f"Citations request failed with status {resp.status_code}")
            return []

        refs = resp.json().get("data") or []
        papers = []
        for ref in refs:
            cited = ref.get("citedPaper", {})
            if not cited or not cited.get("title"):
                continue
            external_ids = cited.get("externalIds") or {}
            papers.append({
                "title": cited.get("title", ""),
                "abstract": cited.get("abstract", "") or "",
                "authors": [a["name"] for a in cited.get("authors", []) if "name" in a],
                "year": cited.get("year"),
                "citation_count": cited.get("citationCount", 0),
                "paper_id": cited.get("paperId", ""),
                "arxiv_id": external_ids.get("ArXiv", ""),
                "source": "semantic_scholar",
            })
        logger.info(f"Found {len(papers)} citations for {paper_id}")
        return papers
    except Exception as e:
        logger.error(f"Citations fetch error: {e}")
        return []
