"""Extractor agent — uses FAST LLM (gemma3:1b) for structured paper extraction."""

import asyncio
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor

from llm_client import call_gemma_fast

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=3)

EXTRACT_PROMPT = """Extract structured info from this research paper.

Title: {title}
Abstract: {abstract}

Return ONLY this JSON:
{{
  "core_claims": ["claim1", "claim2"],
  "methodology": "one sentence",
  "key_results": ["result1", "result2"],
  "limitations": ["limit1"],
  "keywords": ["kw1", "kw2"],
  "domain": "field name"
}}"""


def extract_paper(paper: dict) -> dict:
    """Extract one paper using the FAST model (gemma3:1b)."""
    title = paper.get("title", "")
    abstract = paper.get("abstract", "")

    if not abstract or len(abstract.strip()) < 20:
        logger.warning(f"Skipping extraction for '{title[:40]}' — abstract too short")
        paper.update({"core_claims": [], "methodology": "", "key_results": [],
                      "limitations": [], "keywords": [], "domain": "unknown"})
        return paper

    prompt = EXTRACT_PROMPT.format(
        title=title[:200],
        abstract=(paper.get("full_text") or abstract)[:2000],
    )

    try:
        raw = call_gemma_fast(prompt, json_mode=True)
        raw = re.sub(r"```json|```", "", raw).strip()
        extracted = json.loads(raw)

        paper["core_claims"] = extracted.get("core_claims", [])
        paper["methodology"] = extracted.get("methodology", "")
        paper["key_results"] = extracted.get("key_results", [])
        paper["limitations"] = extracted.get("limitations", [])
        paper["keywords"] = extracted.get("keywords", [])
        paper["domain"] = extracted.get("domain", "unknown")

        logger.info(f"Extracted: '{title[:50]}' → {len(paper['core_claims'])} claims")
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error for '{title[:40]}': {e}")
        paper.update({"core_claims": [], "methodology": "", "key_results": [],
                      "limitations": [], "keywords": [], "domain": "unknown"})
    except Exception as e:
        logger.error(f"Extraction failed for '{title[:40]}': {e}")
        paper.update({"core_claims": [], "methodology": "", "key_results": [],
                      "limitations": [], "keywords": [], "domain": "unknown"})

    return paper


async def extract_all_papers(
    papers: list[dict],
    status_callback=None,
) -> list[dict]:
    """Extract papers in parallel batches using the FAST model.

    Uses ThreadPoolExecutor with 3 workers for ~3x speedup.
    """
    async def emit(event: str, detail: str, progress: int):
        if status_callback:
            await status_callback(event, detail, progress)

    total = len(papers)
    await emit("extracting", f"🧠 Extracting {total} papers (fast model, parallel)...", 56)

    loop = asyncio.get_event_loop()
    extracted = []
    batch_size = 3

    for batch_start in range(0, total, batch_size):
        batch = papers[batch_start:batch_start + batch_size]

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

        done = min(batch_start + batch_size, total)
        progress = 56 + int((done / total) * 15)
        await emit("extracting", f"🧠 Extracted {done}/{total} papers", min(progress, 71))

    await emit("extracting", f"✅ Extraction complete: {len(extracted)} papers", 72)
    return extracted
