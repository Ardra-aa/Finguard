"""
Finguard_rag/retrieval/pre_filter.py
Devna Thunnan — M2: Policy-Aware Pre-Filter

Applies hard boolean constraints to post-filter ChromaDB results:
  1. RBAC: user.role must appear in doc's comma-separated valid_roles string
  2. Jurisdiction: user.jurisdiction must appear in doc's comma-separated jurisdiction string
  3. Temporal: doc.effective_date <= user.reference_date

ChromaDB stores all metadata as flat strings, so role/jurisdiction matching
is done by string containment on the returned metadata, not as a ChromaDB
where() clause (ChromaDB cannot do substring contains on string fields).
"""

from typing import List, Tuple
from datetime import date

from Finguard_rag.schemas.document_schema import UserContext


def passes_pre_filter(metadata: dict, user_context: UserContext) -> bool:
    """
    Return True if a document chunk passes all three hard boolean gates.

    Args:
        metadata:     Flat ChromaDB metadata dict for a single chunk.
        user_context: The requesting user's context.

    Returns:
        True if the chunk is accessible to this user; False otherwise.
    """
    # --- Gate 1: RBAC (role must be in valid_roles CSV) ---
    valid_roles_str = metadata.get("valid_roles", "")
    valid_roles = [r.strip() for r in valid_roles_str.split(",") if r.strip()]
    if user_context.role not in valid_roles:
        return False

    # --- Gate 2: Jurisdiction (user's jurisdiction must appear in doc's CSV) ---
    jurisdiction_str = metadata.get("jurisdiction", "IN")
    jurisdictions = [j.strip() for j in jurisdiction_str.split(",") if j.strip()]
    # GLOBAL jurisdiction matches any user; otherwise user's jurisdiction must be in list
    if "GLOBAL" not in jurisdictions and user_context.jurisdiction not in jurisdictions:
        return False

    # --- Gate 3: Temporal (effective_date <= reference_date) ---
    effective_date_str = metadata.get("effective_date", "1970-01-01")
    try:
        effective_date = date.fromisoformat(effective_date_str)
        if effective_date > user_context.reference_date:
            return False
    except ValueError:
        # If date is malformed, allow through (fail-open for effective_date)
        pass

    return True


def post_filter(
    results: List[Tuple[dict, float]],
    user_context: UserContext,
) -> List[Tuple[dict, float]]:
    """
    Filter a list of (metadata, distance) tuples by the three hard gates.

    Args:
        results:      List of (metadata_dict, distance) from ChromaDB.
        user_context: The requesting user's context.

    Returns:
        Filtered list containing only accessible, temporally valid chunks.
    """
    return [
        (meta, dist)
        for meta, dist in results
        if passes_pre_filter(meta, user_context)
    ]
