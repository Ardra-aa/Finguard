"""
Finguard_rag/retrieval/risk_scorer.py
Devna Thunnan — M4: Risk-Aware Retrieval Scorer

Re-ranks retrieved document chunks using:
    final_score = alpha * semantic_score - beta * risk_score
    alpha = 0.7, beta = 0.3  (configurable via config.yaml)

ChromaDB returns cosine *distance* (0=identical, 2=opposite).
We convert to semantic_score = 1 - distance (so 1=identical).

Drops any chunk with final_score < 0.3 (too risky or irrelevant).
Returns List[RankedDocument] sorted descending by final_score.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import List, Tuple
from datetime import date, datetime

from Finguard_rag.schemas.document_schema import (
    FinancialDocument,
    RankedDocument,
)

# Scoring weights (match config.yaml)
ALPHA = 0.7   # semantic similarity weight
BETA  = 0.3   # risk penalty weight
MIN_FINAL_SCORE = 0.1  # drop anything below this threshold


def _parse_date(date_str: str):
    """Parse ISO date string to date object; return epoch on failure."""
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return date(1970, 1, 1)


def _metadata_to_document(meta: dict) -> FinancialDocument:
    """
    Convert a flat ChromaDB metadata dict back into a FinancialDocument.
    """
    jurisdiction_str = meta.get("jurisdiction", "IN")
    valid_roles_str  = meta.get("valid_roles", "")
    sup_str          = meta.get("superseded_date", "")

    return FinancialDocument(
        doc_id           = meta.get("doc_id", "UNKNOWN"),
        content          = meta.get("_chunk_text", ""),   # attached by versioned_retriever
        jurisdiction     = jurisdiction_str,
        regulatory_scope = meta.get("regulatory_scope", "corporate"),
        valid_roles      = [r.strip() for r in valid_roles_str.split(",") if r.strip()],
        effective_date   = _parse_date(meta.get("effective_date", "1970-01-01")),
        superseded_date  = _parse_date(sup_str) if sup_str else None,
        version          = meta.get("version", "1.0"),
        risk_level       = meta.get("risk_level", "MEDIUM"),
        risk_score       = float(meta.get("risk_score", 0.5)),
        source_file      = meta.get("source_file", ""),
    )


def score_and_rank(
    candidates: List[Tuple[dict, float]],
    alpha: float = ALPHA,
    beta: float  = BETA,
    min_score: float = MIN_FINAL_SCORE,
) -> List[RankedDocument]:
    """
    Score, filter, and rank candidate document chunks.

    Args:
        candidates:  List of (metadata_dict, chroma_distance) tuples.
                     metadata_dict must contain '_chunk_text' (added by versioned_retriever).
        alpha:       Weight for semantic similarity (default 0.7).
        beta:        Weight for risk penalty (default 0.3).
        min_score:   Drop chunks with final_score below this (default 0.3).

    Returns:
        List[RankedDocument] sorted by final_score descending.
        Empty list if no chunks survive the min_score threshold.
    """
    ranked: List[RankedDocument] = []

    for meta, chroma_distance in candidates:
        # Convert ChromaDB cosine distance → similarity score
        # ChromaDB cosine distance ∈ [0, 2]; similarity = 1 - distance
        semantic_score = max(0.0, 1.0 - chroma_distance)

        doc_risk_score = float(meta.get("risk_score", 0.5))

        final_score = alpha * semantic_score - beta * doc_risk_score

        if final_score < min_score:
            continue  # Drop: too risky or not relevant enough

        doc = _metadata_to_document(meta)

        ranked.append(RankedDocument(
            document       = doc,
            semantic_score = round(semantic_score, 4),
            risk_score     = doc_risk_score,
            final_score    = round(final_score, 4),
        ))

    # Sort descending by final_score
    ranked.sort(key=lambda r: r.final_score, reverse=True)
    return ranked
