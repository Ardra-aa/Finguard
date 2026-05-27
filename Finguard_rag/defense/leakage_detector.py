"""
M8 — Role-Inference Leakage Detector
Detects cross-query inference attacks within a single session.

A junior_analyst might ask individually-permitted questions that,
combined over a session, reconstruct salary/board data restricted to ceo/cfo.
This module catches that pattern.
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
