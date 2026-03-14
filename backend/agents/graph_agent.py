"""Graph agent — builds knowledge graph and detects contradictions (optimized)."""

import json
import logging
from itertools import combinations

from embeddings_client import embed_text, embed_texts, cosine_similarity
from llm_client import call_gemini
from graph.knowledge_graph import get_graph

logger = logging.getLogger(__name__)


async def build_knowledge_graph(
    session_id: str,
    papers: list[dict],
    status_callback=None,
) -> dict:
    """Build the knowledge graph from extracted papers.

    Optimized: batch-embeds all claims upfront, then uses cosine similarity
    to find support/contradiction/related edges without per-pair API calls.

    Args:
        session_id: Research session ID.
        papers: List of enriched paper dicts.
        status_callback: Async SSE callback.

    Returns:
        Dict with contradictions list and graph stats.
    """
    async def emit(event: str, detail: str, progress: int):
        if status_callback:
            await status_callback(event, detail, progress)

    kg = get_graph(session_id)
    await emit("graph_building", "🕸️ Building knowledge graph...", 73)

    # Step 1: Add all papers as nodes
    node_ids = {}
    for paper in papers:
        node_id = kg.add_paper(paper)
        if node_id:
            pid = paper.get("paper_id") or paper.get("arxiv_id") or paper.get("title", "")[:60]
            node_ids[pid] = node_id

    await emit("graph_building", f"🕸️ Added {len(node_ids)} nodes to graph", 75)

    # Step 2: Batch-embed all paper claims ONCE (instead of per-pair)
    await emit("graph_building", "🕸️ Computing claim embeddings...", 76)

    claim_texts = []
    paper_keys = []
    for paper in papers:
        claims = " ".join(paper.get("core_claims", []))
        if claims:
            claim_texts.append(claims)
            pid = paper.get("paper_id") or paper.get("arxiv_id") or paper.get("title", "")[:60]
            paper_keys.append(pid)

    # Single batch embedding call
    if claim_texts:
        all_embeddings = embed_texts(claim_texts)
    else:
        all_embeddings = []

    # Build embedding lookup
    embedding_map = {}
    for key, emb in zip(paper_keys, all_embeddings):
        embedding_map[key] = emb

    await emit("graph_building", f"🕸️ Embedded {len(embedding_map)} paper claims", 78)

    # Step 3: Detect relationships using pre-computed embeddings
    contradictions = []
    paper_pairs = list(combinations(papers, 2))
    max_pairs = min(len(paper_pairs), 50)

    # Track pairs that might contradict (for targeted LLM checks)
    potential_contradictions = []

    for pa, pb in paper_pairs[:max_pairs]:
        pid_a = pa.get("paper_id") or pa.get("arxiv_id") or pa.get("title", "")[:60]
        pid_b = pb.get("paper_id") or pb.get("arxiv_id") or pb.get("title", "")[:60]

        nid_a = node_ids.get(pid_a)
        nid_b = node_ids.get(pid_b)
        if not nid_a or not nid_b:
            continue

        emb_a = embedding_map.get(pid_a)
        emb_b = embedding_map.get(pid_b)

        if not emb_a or not emb_b:
            # No claims, check domain match
            domain_a = pa.get("domain", "")
            domain_b = pb.get("domain", "")
            if domain_a and domain_b and domain_a.lower() == domain_b.lower():
                kg.add_related_edge(nid_a, nid_b, similarity=0.5)
            continue

        sim = cosine_similarity(emb_a, emb_b)

        if sim > 0.7:
            # High similarity = support
            kg.add_support_edge(nid_a, nid_b, reason="High claim similarity")
        elif 0.3 <= sim <= 0.7:
            # Medium similarity = potential contradiction, queue for LLM check
            potential_contradictions.append((pa, pb, nid_a, nid_b, sim))
        else:
            # Low similarity, check domain
            domain_a = pa.get("domain", "")
            domain_b = pb.get("domain", "")
            if domain_a and domain_b and domain_a.lower() == domain_b.lower():
                kg.add_related_edge(nid_a, nid_b, similarity=sim)

    await emit(
        "graph_building",
        f"🕸️ Found {len(potential_contradictions)} potential contradictions to verify",
        80,
    )

    # Step 4: Only use LLM for top 5 potential contradictions (capped for speed)
    llm_checks = potential_contradictions[:5]
    for i, (pa, pb, nid_a, nid_b, sim) in enumerate(llm_checks):
        claims_a = " ".join(pa.get("core_claims", []))[:500]
        claims_b = " ".join(pb.get("core_claims", []))[:500]

        prompt = f"""Two research papers make the following claims:

Paper A ({pa.get('year', 'unknown')}): {claims_a}
Paper B ({pb.get('year', 'unknown')}): {claims_b}

Do these papers CONTRADICT each other?
Return JSON: {{"contradicts": true/false, "reason": "one sentence explanation"}}"""

        try:
            result = call_gemini(prompt, json_mode=True)
            data = json.loads(result)
            if data.get("contradicts"):
                kg.add_contradiction_edge(nid_a, nid_b, reason=data.get("reason", ""))
                contradictions.append({
                    "paper_a": pa.get("title", ""),
                    "paper_b": pb.get("title", ""),
                    "reason": data.get("reason", ""),
                    "year_a": pa.get("year"),
                    "year_b": pb.get("year"),
                })
                logger.info(f"Contradiction: '{pa.get('title', '')[:30]}' vs '{pb.get('title', '')[:30]}'")
        except json.JSONDecodeError:
            logger.warning("Failed to parse contradiction detection response")
        except Exception as e:
            logger.error(f"Contradiction detection error: {e}")

        await emit(
            "graph_building",
            f"🕸️ Verified {i+1}/{len(llm_checks)} potential contradictions",
            80 + int((i + 1) / max(len(llm_checks), 1) * 5),
        )

    stats = kg.get_stats()
    await emit(
        "graph_building",
        f"✅ Knowledge graph complete: {stats['num_nodes']} nodes, {stats['num_edges']} edges, {len(contradictions)} contradictions",
        86,
    )

    return {
        "contradictions": contradictions,
        "stats": stats,
    }
