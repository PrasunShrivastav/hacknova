"""Roadmap agent — generates a structured reading roadmap from analyzed papers."""

from llm_client import call_gemini
import json
import logging

logger = logging.getLogger(__name__)

ROADMAP_PROMPT = """You are a research mentor. Given these papers (sorted by year), create a structured reading roadmap for someone who wants to deeply understand this research area.

Papers (title, year, domain):
{papers_list}

Return ONLY this JSON:
{{
  "roadmap": [
    {{
      "stage": "Foundations",
      "description": "Start here — core concepts and definitions",
      "papers": ["exact paper title 1", "exact paper title 2"],
      "why": "These establish the vocabulary and baseline methods"
    }},
    {{
      "stage": "Key Methods",
      "description": "Where the field developed its main approaches",
      "papers": ["exact paper title 3"],
      "why": "Understanding these methods prevents reinventing the wheel"
    }},
    {{
      "stage": "Current Frontier",
      "description": "State of the art as of {max_year}",
      "papers": ["exact paper title 4"],
      "why": "These define what's solved and what isn't"
    }},
    {{
      "stage": "Open Problems",
      "description": "Where YOU can contribute",
      "papers": [],
      "why": "Based on gaps identified in the literature"
    }}
  ],
  "estimated_reading_time": "X hours",
  "suggested_first_paper": "title of the single best entry point"
}}"""


def generate_roadmap(papers: list[dict]) -> dict:
    """Generate a reading roadmap from analyzed papers.

    Args:
        papers: List of enriched paper dicts.

    Returns:
        Dict with roadmap stages, reading time estimate, and suggested first paper.
    """
    if not papers:
        return {"roadmap": [], "estimated_reading_time": "0 hours",
                "suggested_first_paper": ""}

    papers_list = "\n".join([
        f"- {p['title'][:70]} ({p.get('year', '?')}) [{p.get('domain', 'general')}]"
        for p in sorted(papers, key=lambda x: x.get("year") or 0)
    ])
    max_year = max((p.get("year") or 0 for p in papers), default=2024)

    prompt = ROADMAP_PROMPT.format(papers_list=papers_list, max_year=max_year)

    logger.info(f"Generating research roadmap from {len(papers)} papers")

    try:
        raw = call_gemini(prompt, json_mode=True)
        result = json.loads(raw)
        logger.info(f"Roadmap generated: {len(result.get('roadmap', []))} stages")
        return result
    except json.JSONDecodeError:
        logger.warning("Failed to parse roadmap JSON")
        return {"roadmap": [], "error": "Could not generate roadmap"}
    except Exception as e:
        logger.error(f"Roadmap generation failed: {e}")
        return {"roadmap": [], "error": str(e)}
