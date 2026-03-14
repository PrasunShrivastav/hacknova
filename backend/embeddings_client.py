"""Local embeddings client using ChromaDB's built-in embedding function.

Uses chromadb.utils.embedding_functions.DefaultEmbeddingFunction which runs
the all-MiniLM-L6-v2 model via onnxruntime — no PyTorch or CUDA required.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

_embedding_fn = None


def _get_embedding_fn():
    """Lazy-load ChromaDB's default embedding function (downloads ~80MB model on first run)."""
    global _embedding_fn
    if _embedding_fn is None:
        logger.info("Loading ChromaDB DefaultEmbeddingFunction (all-MiniLM-L6-v2 via ONNX)...")
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        _embedding_fn = DefaultEmbeddingFunction()
        logger.info("Embeddings function loaded successfully.")
    return _embedding_fn


def embed_text(text: str) -> list[float]:
    """Embed a single text string into a 384-dimensional vector."""
    ef = _get_embedding_fn()
    result = ef([text])
    return list(result[0])


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts."""
    if not texts:
        return []
    ef = _get_embedding_fn()
    results = ef(texts)
    return [list(r) for r in results]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    a_arr, b_arr = np.array(a), np.array(b)
    norm_a, norm_b = np.linalg.norm(a_arr), np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))
