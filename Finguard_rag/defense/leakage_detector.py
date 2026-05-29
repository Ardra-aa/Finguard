"""
M8 — Role-Inference Leakage Detector
Detects cross-query inference attacks within a single session.

A junior_analyst might ask individually-permitted questions that,
combined over a session, reconstruct salary/board data restricted to ceo/cfo.
This module catches that pattern.

Enhanced: Now includes QUERY-LEVEL sensitivity detection that fires BEFORE
RBAC filtering, so even if docs are blocked, the query intent is flagged.
"""

from __future__ import annotations
from typing import List

from .session_tracker import SessionTracker
from .sensitivity_graph import build_graph, compute_leakage_risk

try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    _EMBED_AVAILABLE = True
except Exception:
    _EMBED_AVAILABLE = False
    _MODEL = None


# ---------------------------------------------------------------------------
# Query-Level Sensitivity Detection (fires BEFORE RBAC / doc retrieval)
# ---------------------------------------------------------------------------
SENSITIVE_PATTERNS = {
    "compensation": ["salary", "ctc", "band 5", "band 6", "package",
                     "compensation", "pay grade", "pay scale", "salary band"],
    "equity":       ["esop", "vesting", "stock option", "equity grant",
                     "rsu", "share allocation"],
    "bonus":        ["bonus", "incentive", "variable pay", "performance pay",
                     "annual increment", "hike"],
    "personal_hr":  ["appraisal", "promotion criteria", "performance rating",
                     "increment", "salary hike"],
}

# Cross-role salary inference patterns — fires BEFORE any other checks
CROSS_ROLE_SALARY_PATTERNS = [
    "salary of", "compensation of", "pay of", "ctc of",
    "how much does", "how much do", "what does a", "what do",
    "executive salary", "manager salary", "senior salary",
    "ceo salary", "cfo salary", "director salary",
    "salary of senior", "salary of executive", "salary of manager",
    "compensation structure", "pay structure",
]


def classify_query_sensitivity(query: str) -> str:
    """
    Classify a query as sensitive based on keywords alone,
    regardless of whether any documents were retrieved.
    Returns "HIGH" if sensitive patterns detected, else "NONE".
    """
    q = query.lower()
    for category, keywords in SENSITIVE_PATTERNS.items():
        if any(kw in q for kw in keywords):
            return "HIGH"
    return "NONE"


def _embed(text: str) -> List[float]:
    if _EMBED_AVAILABLE and _MODEL is not None:
        return _MODEL.encode(text, normalize_embeddings=True).tolist()
    # Deterministic dummy when model unavailable
    import hashlib
    h = hashlib.sha256(text.encode()).digest()
    return [(b / 255.0) for b in h[:32]] + [0.0] * 352


def _infer_doc_sensitivity(doc_ids: List[str]) -> str:
    HIGH_PREFIXES = ("BFS-POL-016", "BFS-POL-017", "BFS-POL-018",
                     "BFS-POL-014", "BFS-POL-015")
    for doc_id in doc_ids:
        for prefix in HIGH_PREFIXES:
            if doc_id.startswith(prefix):
                return "HIGH"
    return "LOW"


class LeakageDetector:
    """M8 main class. Call detect() on every query in a session."""

    def __init__(self) -> None:
        self.tracker = SessionTracker()

    def detect(
        self,
        session_id: str,
        user_id: str,
        role: str,
        query_text: str,
        retrieved_doc_ids: List[str],
        mock_mode: bool = False,
    ) -> dict:
        """
        Returns:
            {
                "leakage_risk":    "NONE" | "LOW" | "HIGH",
                "leakage_details": [str, ...]
            }
        """
        if mock_mode:
            return {"leakage_risk": "NONE", "leakage_details": []}

        # ----- Cross-role salary inference check (fires FIRST) -----
        query_lower = query_text.lower()
        is_cross_role_query = any(p in query_lower for p in CROSS_ROLE_SALARY_PATTERNS)
        is_restricted_role = role in ["junior_analyst", "analyst", "senior_analyst", "it_admin", "auditor_external"]

        if is_cross_role_query and is_restricted_role:
            return {
                "leakage_risk": "HIGH",
                "leakage_details": [
                    f"Cross-role compensation query detected. "
                    f"Role '{role}' is not authorized to query salary/compensation "
                    f"data for other roles. Query: '{query_text[:80]}'"
                ],
            }

        # ----- Query-level sensitivity (fires BEFORE doc-based checks) -----
        query_sensitivity = classify_query_sensitivity(query_text)
        if query_sensitivity == "HIGH":
            # The query itself targets restricted HR/compensation data
            # If the user's role is not authorized for this data, flag immediately
            privileged_roles = {"ceo", "cfo", "hr_manager"}
            if role not in privileged_roles:
                return {
                    "leakage_risk": "HIGH",
                    "leakage_details": [
                        f"Query targets restricted HR/compensation data. "
                        f"Role '{role}' is not authorized for this information. "
                        f"Potential data exfiltration attempt detected."
                    ],
                }

        # ----- Standard doc-based detection (original M8 logic) -----
        embedding   = _embed(query_text)
        sensitivity = _infer_doc_sensitivity(retrieved_doc_ids)

        self.tracker.add_query(
            session_id=session_id,
            user_id=user_id,
            role=role,
            query_text=query_text,
            embedding=embedding,
            sensitivity=sensitivity,
            retrieved_doc_ids=retrieved_doc_ids,
        )

        all_queries = self.tracker.get_queries(session_id)
        graph       = build_graph(all_queries)
        risk_level, details = compute_leakage_risk(graph)

        if risk_level in ("LOW", "HIGH"):
            self.tracker.set_leakage_risk(
                session_id, risk_level, details[0] if details else ""
            )

        return {"leakage_risk": risk_level, "leakage_details": details}
