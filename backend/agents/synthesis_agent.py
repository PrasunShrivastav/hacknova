"""Synthesis agent — generates literature summary, contradiction report, and research gaps."""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from llm_client import call_gemini

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


def generate_literature_summary(papers: list[dict]) -> str:
    """Generate a themed literature summary grouped by topic.

    Args:
        papers: List of enriched paper dicts.

    Returns:
        Markdown-formatted literature summary.
    """
    logger.info(f"Generating literature summary from {len(papers)} papers")

    abstracts = "\n\n".join([
        f"[{i+1}] {p.get('title', 'Untitled')} ({p.get('year', '?')}): {p.get('abstract', '')[:500]}"
        for i, p in enumerate(papers[:30])
    ])

    prompt = f"""You are a research synthesis expert. Given these papers, write a structured literature summary.

Group findings by theme. For each theme:
1. Write a clear theme heading (## Theme Name)
2. Write 2-3 paragraphs synthesizing findings
3. Cite papers as [1], [2] etc.

At the end, include a "## Key Takeaways" section with 3-5 bullet points.

Papers:
{abstracts}

Write the Literature Summary in markdown:"""

    try:
        summary = call_gemini(prompt)
        logger.info(f"Literature summary generated: {len(summary)} chars")
        return summary
    except Exception as e:
        logger.error(f"Literature summary generation failed: {e}")
        return "## Literature Summary\n\nUnable to generate summary due to an error. Please try again."


def generate_contradiction_report(contradictions: list[dict]) -> str:
    """Generate a detailed contradiction report.

    Args:
        contradictions: List of contradiction dicts with paper_a, paper_b, reason.

    Returns:
        Markdown-formatted contradiction report.
    """
    logger.info(f"Generating contradiction report from {len(contradictions)} contradictions")

    if not contradictions:
        return "## Contradiction Report\n\nNo significant contradictions were found in the analyzed literature. The papers generally agree on their core findings."

    items = "\n".join([
        f"- **{c.get('paper_a', 'Paper A')[:60]}** ({c.get('year_a', '?')}) vs **{c.get('paper_b', 'Paper B')[:60]}** ({c.get('year_b', '?')}): {c.get('reason', 'Unknown reason')}"
        for c in contradictions[:15]
    ])

    prompt = f"""Given these contradictions found between research papers, write a clear Contradiction Report in markdown.

For each contradiction explain:
1. What Paper A claims
2. What Paper B claims
3. Why they disagree
4. Which is more recent (and if that matters)

End with a "## Implications" section discussing what these disagreements mean for the field.

Contradictions:
{items}

Write the Contradiction Report:"""

    try:
        report = call_gemini(prompt)
        logger.info(f"Contradiction report generated: {len(report)} chars")
        return report
    except Exception as e:
        logger.error(f"Contradiction report generation failed: {e}")
        return f"## Contradiction Report\n\nFound {len(contradictions)} contradictions but failed to generate detailed report."


def generate_research_gaps(papers: list[dict]) -> str:
    """Identify research gaps and unanswered questions.

    Args:
        papers: List of enriched paper dicts.

    Returns:
        JSON string with ranked research gaps.
    """
    logger.info(f"Identifying research gaps from {len(papers)} papers")

    all_limitations = []
    for p in papers[:25]:
        for lim in p.get("limitations", []):
            all_limitations.append(f"- [{p.get('title', 'Unknown')[:40]}]: {lim}")

    limitations_text = "\n".join(all_limitations) if all_limitations else "No explicit limitations extracted."
    abstracts = "\n".join([p.get("abstract", "")[:300] for p in papers[:20]])

    prompt = f"""You are identifying research gaps. Based on these papers' limitations and abstracts,
identify the top 5 questions that the literature circles around but has NEVER directly answered.

Limitations stated by papers:
{limitations_text}

Paper abstracts:
{abstracts}

Return JSON:
{{
  "gaps": [
    {{"rank": 1, "gap": "description of the gap", "evidence": "why you think this is a gap based on the literature", "importance": "high/medium/low"}},
    {{"rank": 2, "gap": "description", "evidence": "explanation", "importance": "high/medium/low"}},
    {{"rank": 3, "gap": "description", "evidence": "explanation", "importance": "high/medium/low"}},
    {{"rank": 4, "gap": "description", "evidence": "explanation", "importance": "medium/low"}},
    {{"rank": 5, "gap": "description", "evidence": "explanation", "importance": "medium/low"}}
  ]
}}"""

    try:
        result = call_gemini(prompt, json_mode=True)
        # Validate it's valid JSON
        parsed = json.loads(result)
        logger.info(f"Research gaps identified: {len(parsed.get('gaps', []))} gaps")
        return result
    except json.JSONDecodeError:
        logger.warning("Failed to parse research gaps JSON, returning raw text wrapped in JSON")
        return json.dumps({"gaps": [{"rank": 1, "gap": "Unable to parse structured gaps", "evidence": "LLM response was not valid JSON", "importance": "medium"}]})
    except Exception as e:
        logger.error(f"Research gaps generation failed: {e}")
        return json.dumps({"gaps": []})


async def generate_all_outputs(
    papers: list[dict],
    contradictions: list[dict],
    status_callback=None,
) -> dict:
    """Generate all three synthesis outputs with parallelism.

    Summary runs first (largest prompt), then contradictions + gaps run in parallel.

    Args:
        papers: Enriched paper dicts.
        contradictions: Contradiction list from graph agent.
        status_callback: Async SSE callback.

    Returns:
        Dict with 'summary', 'contradictions', 'gaps' keys.
    """
    loop = asyncio.get_event_loop()

    async def emit(event: str, detail: str, progress: int):
        if status_callback:
            await status_callback(event, detail, progress)

    # Step 1: Summary first (heaviest prompt)
    await emit("synthesizing", "✍️ Generating literature summary...", 87)
    summary = await loop.run_in_executor(_executor, generate_literature_summary, papers)

    # Step 2: Contradictions + Gaps in parallel
    await emit("synthesizing", "✍️ Generating contradiction report + research gaps (parallel)...", 92)
    contradiction_future = loop.run_in_executor(
        _executor, generate_contradiction_report, contradictions
    )
    gaps_future = loop.run_in_executor(
        _executor, generate_research_gaps, papers
    )
    contradiction_report, gaps = await asyncio.gather(contradiction_future, gaps_future)

    await emit("synthesizing", "✅ Synthesis complete!", 98)

    return {
        "summary": summary,
        "contradictions": contradiction_report,
        "gaps": gaps,
    }
