"""Extractor agent — uses LLM for structured paper analysis with parallel batching."""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from llm_client import call_gemini

logger = logging.getLogger(__name__)

# Process 3 papers concurrently (Ollama handles queuing internally)
_executor = ThreadPoolExecutor(max_workers=3)

EXTRACT_PROMPT = """You are a research paper analyst. Given the title and abstract of a paper, extract structured information.

Paper Title: {title}
Abstract: {abstract}

Extract and return ONLY this JSON:
{{
  "core_claims": ["claim1", "claim2"],
  "methodology": "brief description of method used",
  "key_results": ["result1", "result2"],
  "limitations": ["limitation1"],
  "keywords": ["kw1", "kw2", "kw3"],
  "domain": "field of study"
}}"""


def extract_paper(paper: dict) -> dict:
    """Extract structured claims, methodology, results, and limitations from a paper.

    Args:
        paper: Paper dict with at least 'title' and 'abstract'.

    Returns:
        The paper dict enriched with extracted fields.
    """
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")

    if not abstract or len(abstract.strip()) < 20:
        logger.warning(f"Skipping extraction for '{title[:40]}' — abstract too short")
        paper.setdefault("core_claims", [])
        paper.setdefault("methodology", "")
        paper.setdefault("key_results", [])
        paper.setdefault("limitations", [])
        paper.setdefault("keywords", [])
        paper.setdefault("domain", "")
        return paper

    prompt = EXTRACT_PROMPT.format(
        title=title,
        abstract=abstract[:2000],  # Limit token usage
    )

    try:
        raw = call_gemini(prompt, json_mode=True)
        extracted = json.loads(raw)

        paper["core_claims"] = extracted.get("core_claims", [])
        paper["methodology"] = extracted.get("methodology", "")
        paper["key_results"] = extracted.get("key_results", [])
        paper["limitations"] = extracted.get("limitations", [])
        paper["keywords"] = extracted.get("keywords", [])
        paper["domain"] = extracted.get("domain", "")

        logger.info(f"Extracted: '{title[:40]}' → {len(paper['core_claims'])} claims, domain={paper['domain']}")
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error for '{title[:40]}': {e}")
        paper.setdefault("core_claims", [])
        paper.setdefault("methodology", "")
        paper.setdefault("key_results", [])
        paper.setdefault("limitations", [])
        paper.setdefault("keywords", [])
        paper.setdefault("domain", "")
    except Exception as e:
        logger.error(f"Extraction failed for '{title[:40]}': {e}")
        paper.setdefault("core_claims", [])
        paper.setdefault("methodology", "")
        paper.setdefault("key_results", [])
        paper.setdefault("limitations", [])
        paper.setdefault("keywords", [])
        paper.setdefault("domain", "")

    return paper


async def extract_all_papers(
    papers: list[dict],
    status_callback=None,
) -> list[dict]:
    """Extract structured information from all papers using parallel batching.

    Papers are processed in batches of 3 concurrently via ThreadPoolExecutor.

    Args:
        papers: List of paper dicts.
        status_callback: Async callback for SSE updates.

    Returns:
        List of enriched paper dicts.
    """
    async def emit(event: str, detail: str, progress: int):
        if status_callback:
            await status_callback(event, detail, progress)

    total = len(papers)
    await emit("extracting", f"🧠 Extracting structured data from {total} papers (parallel)...", 56)

    loop = asyncio.get_event_loop()
    extracted = []
    batch_size = 3

    for batch_start in range(0, total, batch_size):
        batch = papers[batch_start:batch_start + batch_size]

        # Run batch concurrently
        futures = [
            loop.run_in_executor(_executor, extract_paper, paper)
            for paper in batch
        ]
        results = await asyncio.gather(*futures, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Extraction error for paper {batch_start + i}: {result}")
                extracted.append(batch[i])
            else:
                extracted.append(result)

        # Progress update after each batch
        done = min(batch_start + batch_size, total)
        progress = 56 + int((done / total) * 15)
        await emit(
            "extracting",
            f"🧠 Extracted {done}/{total} papers",
            min(progress, 71),
        )

    await emit("extracting", f"✅ Extraction complete: {len(extracted)} papers processed", 72)
    return extracted
