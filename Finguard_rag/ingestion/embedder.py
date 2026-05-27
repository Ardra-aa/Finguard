"""
Finguard_rag/ingestion/embedder.py
Devna Thunnan — M1: Document Ingestion & Corpus Builder

Loads sentence-transformers all-MiniLM-L6-v2 locally (no API key needed,
~90 MB download on first use). Provides embed_texts() for batch embedding.
"""

from sentence_transformers import SentenceTransformer
from typing import List

MODEL_NAME = "all-MiniLM-L6-v2"

# Load model once at module level (cached for the process lifetime)
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model (singleton pattern)."""
    global _model
    if _model is None:
        print(f"[embedder] Loading model '{MODEL_NAME}' (first call only)...")
        _model = SentenceTransformer(MODEL_NAME)
        print(f"[embedder] Model loaded. Embedding dimension: {_model.get_sentence_embedding_dimension()}")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of text strings into 384-dimensional vectors.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each a List[float] of length 384).
    """
    if not texts:
        return []
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """
    Embed a single query string.

    Args:
        query: Query text.

    Returns:
        Single embedding vector (List[float] of length 384).
    """
    return embed_texts([query])[0]
