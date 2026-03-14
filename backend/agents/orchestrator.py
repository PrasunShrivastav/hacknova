"""Orchestrator — coordinates all agents for a complete research pipeline."""

import asyncio
import json
import logging
import uuid
from typing import Optional

from agents.crawler_agent import crawl_papers
from agents.extractor_agent import extract_all_papers
from agents.graph_agent import build_knowledge_graph
from agents.synthesis_agent import generate_all_outputs
from vector.chroma_store import store_papers
from graph.knowledge_graph import get_graph

logger = logging.getLogger(__name__)

# Global session state
_sessions: dict[str, dict] = {}
_status_queues: dict[str, asyncio.Queue] = {}


def get_session(session_id: str) -> Optional[dict]:
    """Get a session's state."""
    return _sessions.get(session_id)


def create_session(question: str) -> str:
    """Create a new research session.

    Args:
        question: The research question.

    Returns:
        Newly created session ID.
    """
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "session_id": session_id,
        "question": question,
        "status": "pending",
        "papers": [],
        "summary": "",
        "contradictions": "",
        "gaps": "",
        "error": None,
    }
    _status_queues[session_id] = asyncio.Queue()
    logger.info(f"Created session {session_id} for question: '{question[:60]}'")
    return session_id


def get_status_queue(session_id: str) -> Optional[asyncio.Queue]:
    """Get the SSE status queue for a session."""
    return _status_queues.get(session_id)


def _filter_relevant_papers(papers: list[dict], query: str) -> tuple[list[dict], list[dict]]:
    """Fast relevance filter using embeddings. No LLM calls.

    Compares each paper's title+abstract against the query using cosine similarity.
    Returns (relevant_papers, all_papers_with_scores).

    Papers scoring >= 0.35 similarity are considered relevant.
    """
    from embeddings_client import embed_text, embed_texts, cosine_similarity

    query_emb = embed_text(query)

    # Batch-embed all papers at once
    texts = [f"{p.get('title', '')}. {p.get('abstract', '')[:300]}" for p in papers]
    all_embeddings = embed_texts(texts)

    scored = []
    for paper, emb in zip(papers, all_embeddings):
        score = cosine_similarity(query_emb, emb)
        paper["relevance_score"] = round(score, 3)
        scored.append((score, paper))

    # Sort by relevance
    scored.sort(key=lambda x: x[0], reverse=True)

    # Keep papers with similarity >= 0.35,  but always keep at least 5
    relevant = [p for s, p in scored if s >= 0.35]
    if len(relevant) < 5:
        relevant = [p for _, p in scored[:5]]

    all_papers = [p for _, p in scored]

    logger.info(
        f"Relevance filter: {len(relevant)}/{len(papers)} papers passed "
        f"(scores: {scored[0][0]:.2f} to {scored[-1][0]:.2f})"
    )

    return relevant, all_papers


async def run_research_pipeline(
    session_id: str,
    max_papers: int = 30,
    depth: int = 2,
):
    """Run the full ARIA research pipeline asynchronously.

    Stages:
    1. Crawl papers from arXiv + Semantic Scholar + PubMed
    2. FILTER: Remove off-topic papers using embedding similarity
    3. Extract structured data from relevant papers using LLM
    4. Build knowledge graph and detect contradictions
    5. Generate synthesis outputs (summary, contradiction report, gaps)

    Args:
        session_id: The session ID to run the pipeline for.
        max_papers: Maximum papers to collect.
        depth: Citation trail depth.
    """
    session = _sessions.get(session_id)
    if not session:
        logger.error(f"Session {session_id} not found")
        return

    session["status"] = "running"
    queue = _status_queues.get(session_id)

    async def status_callback(event: str, detail: str, progress: int):
        """Push status events to the SSE queue."""
        if queue:
            await queue.put({
                "event": event,
                "detail": detail,
                "progress": progress,
            })

    try:
        question = session["question"]

        # === STAGE 1: CRAWL ===
        await status_callback("started", f"🚀 Starting research on: {question[:80]}", 1)
        papers = await crawl_papers(
            query=question,
            max_papers=max_papers,
            depth=depth,
            status_callback=status_callback,
        )

        if not papers:
            raise Exception("No papers found for the given query. Try a different search term.")

        # === STAGE 2: RELEVANCE FILTER (fast, no LLM) ===
        await status_callback("filtering", "🎯 Filtering for relevant papers...", 56)
        relevant_papers, all_papers_scored = _filter_relevant_papers(papers, question)

        filtered_out = len(papers) - len(relevant_papers)
        await status_callback(
            "filtering",
            f"🎯 Kept {len(relevant_papers)} relevant papers, filtered out {filtered_out} off-topic",
            58,
        )

        # Store ALL papers for the papers tab (with relevance scores)
        session["papers"] = all_papers_scored

        # === STAGE 3: EXTRACT (only relevant papers) ===
        relevant_papers = await extract_all_papers(
            papers=relevant_papers,
            status_callback=status_callback,
        )

        # Update session with enriched relevant papers + unenriched others
        relevant_ids = {p.get("title", "")[:60] for p in relevant_papers}
        final_papers = list(relevant_papers)  # relevant first
        for p in all_papers_scored:
            if p.get("title", "")[:60] not in relevant_ids:
                final_papers.append(p)
        session["papers"] = final_papers

        # Store in ChromaDB for later Q&A (only relevant)
        await status_callback("indexing", "📂 Indexing papers in vector database...", 72)
        store_papers(session_id, relevant_papers)

        # === STAGE 4: BUILD GRAPH (only relevant papers) ===
        graph_result = await build_knowledge_graph(
            session_id=session_id,
            papers=relevant_papers,
            status_callback=status_callback,
        )

        # === STAGE 5: SYNTHESIZE (only relevant papers) ===
        outputs = await generate_all_outputs(
            papers=relevant_papers,
            contradictions=graph_result.get("contradictions", []),
            status_callback=status_callback,
        )

        # Store results
        session["summary"] = outputs["summary"]
        session["contradictions"] = outputs["contradictions"]
        session["gaps"] = outputs["gaps"]
        session["status"] = "completed"

        # Strip embeddings from papers for API response
        session["papers"] = [
            {k: v for k, v in p.items() if k != "embedding"}
            for p in final_papers
        ]

        await status_callback("completed", f"🎉 Research complete! Analyzed {len(relevant_papers)} relevant papers (from {len(all_papers_scored)} total).", 100)
        logger.info(f"Session {session_id} completed: {len(relevant_papers)} relevant / {len(all_papers_scored)} total papers")

    except Exception as e:
        logger.error(f"Pipeline error for session {session_id}: {e}", exc_info=True)
        session["status"] = "failed"
        session["error"] = str(e)
        if queue:
            await queue.put({
                "event": "error",
                "detail": f"❌ Pipeline failed: {str(e)}",
                "progress": -1,
            })

    finally:
        # Signal SSE stream to close
        if queue:
            await queue.put(None)
