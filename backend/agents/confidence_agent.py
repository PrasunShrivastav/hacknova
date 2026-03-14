"""Confidence agent — scores each claim by how many other papers corroborate it."""

import logging
from embeddings_client import embed_texts, cosine_similarity

logger = logging.getLogger(__name__)


def score_claims(papers: list[dict]) -> list[dict]:
    """Score every claim's confidence based on cross-paper corroboration.

    For each paper's core_claims, check how many OTHER papers make a similar claim.
    More corroboration = higher confidence.
    Score: 0.0 (lone wolf) → 1.0 (universally supported, 5+ papers agree).

    Uses batch embeddings for speed.
    """
    # Build flat list of all claims
    all_claims = []
    for p in papers:
        for claim in p.get("core_claims", []):
            if claim and len(claim.strip()) > 5:
                all_claims.append({
                    "claim": claim,
                    "paper_title": p.get("title", ""),
                    "year": p.get("year"),
                })

    if not all_claims:
        logger.info("No claims to score")
        return papers

    # Batch-embed all claims at once
    claim_texts = [c["claim"][:300] for c in all_claims]
    embeddings = embed_texts(claim_texts)

    # Score each claim against all others using the embeddings list directly
    for i, claim_obj in enumerate(all_claims):
        support_count = 0
        supporting_papers = []

        for j in range(len(all_claims)):
            if i == j or all_claims[j]["paper_title"] == claim_obj["paper_title"]:
                continue

            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim > 0.72:
                support_count += 1
                paper_name = all_claims[j]["paper_title"][:40]
                if paper_name not in supporting_papers:
                    supporting_papers.append(paper_name)

        claim_obj["confidence"] = round(min(1.0, support_count / 5.0), 2)
        claim_obj["support_count"] = support_count
        claim_obj["supported_by"] = supporting_papers[:3]

    # Attach scored claims back to papers
    for p in papers:
        p["scored_claims"] = [
            c for c in all_claims if c["paper_title"] == p.get("title", "")
        ]

    total_scored = len(all_claims)
    high_conf = sum(1 for c in all_claims if c["confidence"] >= 0.6)
    logger.info(f"Scored {total_scored} claims: {high_conf} high confidence")

    return papers
