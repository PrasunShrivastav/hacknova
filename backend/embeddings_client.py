"""Local embeddings client using sentence-transformers (no API key needed)."""

import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

_model = None


def get_embedder() -> SentenceTransformer:
    """Lazy-load the sentence-transformers model (downloads ~80MB on first run)."""
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model 'all-MiniLM-L6-v2'...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embeddings model loaded successfully.")
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string into a 384-dimensional vector."""
    embedder = get_embedder()
    return embedder.encode(text, convert_to_numpy=True).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts."""
    if not texts:
        return []
    embedder = get_embedder()
    return embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False).tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    a_arr, b_arr = np.array(a), np.array(b)
    norm_a, norm_b = np.linalg.norm(a_arr), np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))
