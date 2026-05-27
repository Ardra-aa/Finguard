"""
defense/interface.py
====================
PUBLIC INTERFACE FOR M8 + M9.

Teammates (Amala's retrieval, Devna's generation) call ONLY this function.
They must NOT import LeakageDetector or ConflictResolver directly.

Usage:
    from Finguard_rag.defense.interface import defend, DefenseResult

    result: DefenseResult = defend(
        session_id   = ctx.session_id,
        user_id      = ctx.user_id,
        role         = ctx.role,
        query        = query_text,
        response     = generated_answer,
        source_docs  = ranked_docs,          # List[RankedDocument]
        user_context = ctx,
        mock_mode    = False,
    )
"""

from __future__ import annotations
from typing import List, TYPE_CHECKING

from .leakage_detector import LeakageDetector
from .conflict_resolver import ConflictResolver

if TYPE_CHECKING:
    from ..schemas.document_schema import RankedDocument, UserContext

# Module-level singletons (created once per process)
_leakage_detector  = LeakageDetector()
_conflict_resolver = ConflictResolver()


def defend(
    session_id: str,
    user_id: str,
    role: str,
    query: str,
    response: str,
    source_docs: "List[RankedDocument]",
    user_context: "UserContext | None" = None,
    mock_mode: bool = False,
) -> dict:
    """
    Run M8 (leakage detection) + M9 (conflict resolution) in sequence.

    Parameters
    ----------
    session_id   : unique ID for the current browser/API session
    user_id      : authenticated user identifier
    role         : user's RBAC role
    query        : raw query text
    response     : generated answer text (from generation module)
    source_docs  : List[RankedDocument] retrieved by the retrieval module
    user_context : UserContext dataclass (optional, for future expansion)
    mock_mode    : if True, return safe defaults immediately (useful for unit tests)

    Returns
    -------
    dict matching DefenseResult fields:
        {
            "leakage_risk":                "NONE" | "LOW" | "HIGH",
            "leakage_details":             List[str],
            "conflict_detected":           bool,
            "conflicting_rules":           List[str],
            "conservative_recommendation": str,
        }
    """
    # ------------------------------------------------------------------ M8
    retrieved_doc_ids = [rd.document.doc_id for rd in source_docs]
    leakage_result = _leakage_detector.detect(
        session_id       = session_id,
        user_id          = user_id,
        role             = role,
        query_text       = query,
        retrieved_doc_ids= retrieved_doc_ids,
        mock_mode        = mock_mode,
    )

    # ------------------------------------------------------------------ M9
    source_contents = [rd.document.content for rd in source_docs]
    conflict_result = _conflict_resolver.resolve(
        query            = query,
        source_doc_ids   = retrieved_doc_ids,
        source_contents  = source_contents,
        user_jurisdiction= (user_context.jurisdiction if user_context else "IN"),
        mock_mode        = mock_mode,
    )

    return {
        "leakage_risk":                leakage_result["leakage_risk"],
        "leakage_details":             leakage_result["leakage_details"],
        "conflict_detected":           conflict_result["conflict_detected"],
        "conflicting_rules":           conflict_result["conflicting_rules"],
        "conservative_recommendation": conflict_result["conservative_recommendation"],
    }
