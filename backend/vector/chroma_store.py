"""ChromaDB vector store for paper embeddings — local, no server needed."""

import chromadb
import logging
from embeddings_client import embed_texts

logger = logging.getLogger(__name__)

# Persistent local ChromaDB client
_client = chromadb.Client()  # In-memory; use PersistentClient("./chroma_data") for disk


def _get_collection(session_id: str):
    """Get or create a ChromaDB collection for a session."""
    safe_name = session_id.replace("-", "_")[:50]
    return _client.get_or_create_collection(
        name=f"aria_{safe_name}",
        metadata={"hnsw:space": "cosine"},
    )


def store_papers(session_id: str, papers: list[dict]) -> int:
    """Store paper embeddings in ChromaDB for a given session.

    Uses batch embedding for speed (1 call instead of N).

    Args:
        session_id: Research session ID.
        papers: List of paper dicts (must have 'title' and 'abstract').

    Returns:
        Number of papers successfully stored.
    """
    collection = _get_collection(session_id)

    # Prepare batch data
    texts = []
    doc_ids = []
    metadatas = []

    for i, paper in enumerate(papers):
        text = f"{paper.get('title', '')}. {paper.get('abstract', '')}"
        if not text.strip() or text.strip() == ".":
            continue

        doc_id = paper.get("paper_id") or paper.get("arxiv_id") or f"paper_{i}"
        texts.append(text[:5000])
        doc_ids.append(doc_id)
        metadatas.append({
            "title": (paper.get("title", "") or "")[:500],
            "year": paper.get("year") or 0,
            "source": paper.get("source", "unknown"),
            "authors": ", ".join(paper.get("authors", [])[:5]),
            "index": i,
        })

    if not texts:
        return 0

    try:
        # Single batch embedding call
        embeddings = embed_texts(texts)

        collection.upsert(
            ids=doc_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        stored = len(doc_ids)
        logger.info(f"Stored {stored}/{len(papers)} papers in ChromaDB for session {session_id}")
        return stored
    except Exception as e:
        logger.error(f"Failed to batch-store papers: {e}")
        return 0


def query_papers(session_id: str, query: str, top_k: int = 5) -> list[dict]:
    """Query ChromaDB for the most relevant papers to a question.

    Args:
        session_id: Research session ID.
        query: Natural language query.
        top_k: Number of results to return.

    Returns:
        List of paper dicts sorted by relevance.
    """
    collection = _get_collection(session_id)

    if collection.count() == 0:
        logger.warning(f"No papers in ChromaDB for session {session_id}")
        return []

    try:
        from embeddings_client import embed_text
        query_embedding = embed_text(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        papers = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            papers.append({
                "title": meta.get("title", ""),
                "abstract": results["documents"][0][i] if results["documents"] else "",
                "year": meta.get("year"),
                "source": meta.get("source", ""),
                "authors": meta.get("authors", "").split(", "),
                "relevance_score": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
            })

        logger.info(f"ChromaDB query returned {len(papers)} results for: '{query[:50]}'")
        return papers
    except Exception as e:
        logger.error(f"ChromaDB query error: {e}")
        return []


def delete_session(session_id: str):
    """Delete all data for a session."""
    safe_name = session_id.replace("-", "_")[:50]
    try:
        _client.delete_collection(name=f"aria_{safe_name}")
        logger.info(f"Deleted ChromaDB collection for session {session_id}")
    except Exception as e:
        logger.warning(f"Failed to delete collection: {e}")
