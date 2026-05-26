"""
Finguard_rag/retrieval/versioned_retriever.py
Devna Thunnan — M3: Time-Versioned Retrieval

Queries ChromaDB with an embedding vector, then post-filters results to keep
only document chunks where:
  - effective_date <= reference_date          (doc is in effect)
  - superseded_date == '' OR
    superseded_date > reference_date          (doc not yet superseded)

Returns the top_k valid results as List[Tuple[metadata_dict, distance]].
Distance is the raw ChromaDB cosine distance (lower = more similar).
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import List, Optional, Tuple
from datetime import date

import chromadb

from Finguard_rag.schemas.document_schema import UserContext

CHROMA_PATH = _REPO_ROOT / "data" / "chroma_db"
COLLECTION  = "finguard_docs"

# Singleton ChromaDB client
_client: Optional[chromadb.PersistentClient] = None
_collection = None


def _get_collection():
    """Lazy-load ChromaDB collection (singleton)."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        _collection = _client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _is_version_valid(metadata: dict, reference_date: date) -> bool:
    """
    Check temporal validity for a single chunk's metadata.

    Returns True if:
        effective_date <= reference_date
        AND (superseded_date is empty OR superseded_date > reference_date)
    """
    # Effective date check
    eff_str = metadata.get("effective_date", "1970-01-01")
    try:
        eff_date = date.fromisoformat(eff_str)
        if eff_date > reference_date:
            return False
    except ValueError:
        pass  # Malformed date: fail-open

    # Superseded date check
    sup_str = metadata.get("superseded_date", "")
    if sup_str:  # Non-empty means it was superseded at some point
        try:
            sup_date = date.fromisoformat(sup_str)
            if sup_date <= reference_date:
                return False  # Document is superseded as of reference_date
        except ValueError:
            pass  # Malformed: fail-open

    return True


def versioned_query(
    query_embedding: List[float],
    user_context: UserContext,
    n_candidates: int = 50,
    top_k: int = 10,
) -> List[Tuple[dict, float]]:
    """
    Query ChromaDB and post-filter to time-valid document versions.

    Args:
        query_embedding: 384-dim embedding vector of the user's query.
        user_context:    UserContext (reference_date used for temporal gating).
        n_candidates:    Number of raw results to fetch from ChromaDB before filtering.
        top_k:           Maximum results to return after temporal filtering.

    Returns:
        List of (metadata_dict, distance) tuples, at most top_k,
        sorted by distance ascending (closest first).
    """
    collection = _get_collection()

    if collection.count() == 0:
        print("[versioned_retriever] WARNING: Collection is empty. Run ingestor first.")
        return []

    # Fetch a broad candidate set from ChromaDB
    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_candidates, collection.count()),
        include=["metadatas", "distances", "documents"],
    )

    metadatas  = raw["metadatas"][0]   # List[dict]
    distances  = raw["distances"][0]   # List[float]
    documents  = raw["documents"][0]   # List[str] — chunk text

    # Post-filter: keep only temporally valid versions
    valid_results: List[Tuple[dict, float]] = []
    for meta, dist, doc in zip(metadatas, distances, documents):
        if _is_version_valid(meta, user_context.reference_date):
            # Attach the document text into metadata for downstream use
            meta = dict(meta)
            meta["_chunk_text"] = doc
            valid_results.append((meta, dist))

    # Already sorted by distance (ascending = most similar first)
    return valid_results[:top_k]
