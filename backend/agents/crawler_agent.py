"""Crawler agent — searches arXiv, Semantic Scholar, PubMed in parallel and follows citation trails."""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from tools.arxiv_tool import search_arxiv
from tools.semantic_scholar_tool import search_semantic_scholar, get_citations
from tools.pubmed_tool import search_pubmed

logger = logging.getLogger(__name__)

# Shared executor for blocking I/O calls
_executor = ThreadPoolExecutor(max_workers=4)


def deduplicate_papers(papers: list[dict]) -> list[dict]:
    """Remove duplicate papers based on title similarity."""
    seen_titles = set()
    unique = []
    for p in papers:
        title_key = p.get("title", "").lower().strip()[:80]
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique.append(p)
    return unique


async def crawl_papers(
    query: str,
    max_papers: int = 30,
    depth: int = 2,
    status_callback=None,
) -> list[dict]:
    """Crawl papers from multiple sources IN PARALLEL and follow citation trails.

    Args:
        query: Research question or topic.
        max_papers: Maximum total papers to collect.
        depth: How many levels of citation trails to follow (0-3).
        status_callback: Async function(event, detail, progress) for SSE updates.

    Returns:
        Deduplicated list of paper dicts.
    """
    async def emit(event: str, detail: str, progress: int):
        if status_callback:
            await status_callback(event, detail, progress)

    all_papers = []
    per_source = 5  # Keep small: fewer, more relevant papers = better synthesis
    loop = asyncio.get_event_loop()

    # --- PARALLEL: All 3 sources at once ---
    await emit("crawling", f"🔍 Searching arXiv + Semantic Scholar + PubMed in parallel...", 5)

    async def fetch_arxiv():
        try:
            papers = await loop.run_in_executor(_executor, lambda: search_arxiv(query, max_results=per_source))
            logger.info(f"arXiv: {len(papers)} papers found")
            return papers
        except Exception as e:
            logger.error(f"arXiv crawl failed: {e}")
            return []

    async def fetch_semantic_scholar():
        try:
            papers = await loop.run_in_executor(_executor, lambda: search_semantic_scholar(query, max_results=per_source))
            logger.info(f"Semantic Scholar: {len(papers)} papers found")
            return papers
        except Exception as e:
            logger.error(f"Semantic Scholar crawl failed: {e}")
            return []

    async def fetch_pubmed():
        try:
            papers = await loop.run_in_executor(_executor, lambda: search_pubmed(query, max_results=per_source))
            logger.info(f"PubMed: {len(papers)} papers found")
            return papers
        except Exception as e:
            logger.error(f"PubMed crawl failed: {e}")
            return []

    # Run all 3 concurrently
    arxiv_papers, ss_papers, pubmed_papers = await asyncio.gather(
        fetch_arxiv(),
        fetch_semantic_scholar(),
        fetch_pubmed(),
    )

    all_papers.extend(arxiv_papers)
    all_papers.extend(ss_papers)
    all_papers.extend(pubmed_papers)

    await emit(
        "crawling",
        f"📚 Found {len(arxiv_papers)} arXiv + {len(ss_papers)} S2 + {len(pubmed_papers)} PubMed papers",
        38,
    )

    # Deduplicate before following citations
    all_papers = deduplicate_papers(all_papers)
    await emit("crawling", f"📚 {len(all_papers)} unique papers after deduplication", 40)

    # --- Citation trails ---
    if depth > 0:
        await emit("crawling", f"🔗 Following citation trails (depth={depth})...", 42)
        citation_papers = []

        ss_ids = [
            p["paper_id"] for p in all_papers
            if p.get("paper_id") and p.get("source") == "semantic_scholar"
        ][:10]

        for i, paper_id in enumerate(ss_ids):
            if len(all_papers) + len(citation_papers) >= max_papers:
                break
            try:
                refs = await loop.run_in_executor(_executor, lambda pid=paper_id: get_citations(pid))
                citation_papers.extend(refs)
                progress = 42 + int((i / max(len(ss_ids), 1)) * 10)
                await emit("crawling", f"🔗 Followed {i+1}/{len(ss_ids)} citation trails (+{len(citation_papers)} papers)", progress)
            except Exception as e:
                logger.error(f"Citation trail error for {paper_id}: {e}")

        # Depth 2: follow citations of citations
        if depth >= 2 and citation_papers:
            await emit("crawling", "🔗 Following citation trails (depth 2)...", 53)
            depth2_ids = [
                p["paper_id"] for p in citation_papers
                if p.get("paper_id")
            ][:5]

            for paper_id in depth2_ids:
                if len(all_papers) + len(citation_papers) >= max_papers:
                    break
                try:
                    refs = await loop.run_in_executor(_executor, lambda pid=paper_id: get_citations(pid))
                    citation_papers.extend(refs)
                except Exception as e:
                    logger.error(f"Depth-2 citation error: {e}")

        all_papers.extend(citation_papers)

    # Final dedup and trim
    all_papers = deduplicate_papers(all_papers)[:max_papers]
    await emit("crawling", f"✅ Crawling complete: {len(all_papers)} unique papers collected", 55)
    logger.info(f"Crawl complete: {len(all_papers)} unique papers")

    return all_papers
