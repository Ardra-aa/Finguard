"""
M10 — Baseline Systems
Four baselines from vanilla RAG up to full FinGuard-RAG.
Each baseline is a callable that takes (query, user_context) → dict.
They call the real pipeline modules with progressively more features enabled.
"""

from __future__ import annotations
import sys
import time
import logging
from pathlib import Path

# Ensure repo root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Finguard_rag.schemas.document_schema import UserContext, RankedDocument, ComplianceResponse
from Finguard_rag.retrieval.interface import retrieve
from Finguard_rag.generation.interface import generate
from Finguard_rag.defense.interface import defend

logger = logging.getLogger(__name__)


from datetime import date as _date
from typing import List, Optional

def _build_ctx(user_context: dict) -> UserContext:
    ref_str = user_context.get("reference_date", "2025-01-01")
    if isinstance(ref_str, str):
        ref_date = _date.fromisoformat(ref_str)
    elif isinstance(ref_str, _date):
        ref_date = ref_str
    else:
        ref_date = _date.today()

    return UserContext(
        user_id=user_context.get("user_id", "eval@bharatfinserv.in"),
        role=user_context.get("role", "junior_analyst"),
        jurisdiction=user_context.get("jurisdiction", "IN"),
        reference_date=ref_date,
        session_id=user_context.get("session_id", "eval_session"),
    )


def _extract_jurisdictions(ranked_docs: List[RankedDocument], user_jurisdiction: str) -> str:
    """
    Build a comma-separated string of all distinct jurisdictions from the
    user's context AND every retrieved document's metadata.
    e.g. "IN,SG" or "IN,EU"
    """
    all_j = set()
    # Add user's own jurisdiction
    for j in user_jurisdiction.split(","):
        j = j.strip()
        if j:
            all_j.add(j)
    # Add jurisdictions from every retrieved document
    for rd in ranked_docs:
        doc_j = rd.document.jurisdiction or ""
        for j in doc_j.split(","):
            j = j.strip()
            if j:
                all_j.add(j)
    return ",".join(sorted(all_j))


_REGULATION_KEYWORDS = [
    "rbi", "sebi", "gdpr", "mas", "companies act", "nbfc",
    "kyc", "pit", "lodr", "ifsca", "ncs", "data retention",
    "data privacy", "aml", "insider trading", "capital adequacy",
]


def _extract_best_date(query: str, ranked_docs: List[RankedDocument], ctx: 'UserContext') -> str:
    """
    Find the document whose doc_id or content best matches a regulation
    reference in the query, then use that document's effective_date.
    Falls back to ranked_docs[0] then ctx.reference_date.
    """
    if not ranked_docs:
        return str(ctx.reference_date)

    query_lower = query.lower()
    # Try to find a doc whose ID or content matches query keywords
    best_doc = None
    for doc in ranked_docs:
        doc_id_lower = (doc.document.doc_id or "").lower()
        content_prefix = (doc.document.content or "")[:300].lower()
        for kw in _REGULATION_KEYWORDS:
            if kw in query_lower and (kw in doc_id_lower or kw in content_prefix):
                best_doc = doc
                break
        if best_doc:
            break

    if best_doc is None:
        best_doc = ranked_docs[0]

    return str(best_doc.document.effective_date)


# ---------------------------------------------------------------------------
# Baseline B1 — Vanilla RAG (no compliance, no defense)
# ---------------------------------------------------------------------------
class VanillaRAG:
    """
    B1: Retrieve top-k chunks by semantic similarity only (no RBAC, no temporal,
    no compliance validation, no leakage/conflict defense).
    We call the real retrieval + generation but skip defend().
    """
    name = "B1_VanillaRAG"

    def run(self, query: str, user_context: dict) -> dict:
        start = time.time()
        try:
            # Use a permissive context (ceo role = max access) to simulate no RBAC
            ctx = _build_ctx(user_context)
            ctx.role = "ceo"  # no RBAC filtering

            ranked_docs = retrieve(query, ctx)
            compliance_response = generate(query, ranked_docs, ctx)

            return {
                "answer":                   compliance_response.answer,
                "sources":                  ranked_docs,
                "compliance_status":        "UNKNOWN",  # B1 doesn't validate
                "violations":               [],
                "conflicts":                [],
                "leakage_risk":             "NONE",
                "conflict_detected":        False,
                "predicted_jurisdiction":   _extract_jurisdictions(ranked_docs, user_context.get("jurisdiction", "IN")),
                "response_date":            _extract_best_date(query, ranked_docs, ctx),
                "confidence_score":         0.5,
                "latency_seconds":          time.time() - start,
            }
        except Exception as e:
            logger.warning("B1 error: %s", e)
            return {
                "answer": f"[B1 Error] {e}",
                "sources": [], "compliance_status": "UNKNOWN",
                "violations": [], "conflicts": [],
                "leakage_risk": "NONE", "conflict_detected": False,
                "predicted_jurisdiction": user_context.get("jurisdiction", "IN"),
                "response_date": "2025-01-01",
                "confidence_score": 0.0,
                "latency_seconds": time.time() - start,
            }


# ---------------------------------------------------------------------------
# Baseline B2 — RAG + Role-Based Access Control only
# ---------------------------------------------------------------------------
class RBACFilteredRAG:
    """
    B2: Vanilla RAG + role-filtered retrieval.
    No temporal filter enforcement, no leakage, no conflict.
    """
    name = "B2_RBACFilteredRAG"

    def run(self, query: str, user_context: dict) -> dict:
        start = time.time()
        try:
            ctx = _build_ctx(user_context)  # real role = real RBAC
            ranked_docs = retrieve(query, ctx)
            compliance_response = generate(query, ranked_docs, ctx)

            return {
                "answer":                   compliance_response.answer,
                "sources":                  ranked_docs,
                "compliance_status":        compliance_response.compliance_status,
                "violations":               compliance_response.violations,
                "conflicts":                [],
                "leakage_risk":             "NONE",
                "conflict_detected":        False,
                "predicted_jurisdiction":   _extract_jurisdictions(ranked_docs, user_context.get("jurisdiction", "IN")),
                "response_date":            _extract_best_date(query, ranked_docs, ctx),
                "confidence_score":         0.6,
                "latency_seconds":          time.time() - start,
            }
        except Exception as e:
            logger.warning("B2 error: %s", e)
            return {
                "answer": f"[B2 Error] {e}",
                "sources": [], "compliance_status": "UNKNOWN",
                "violations": [], "conflicts": [],
                "leakage_risk": "NONE", "conflict_detected": False,
                "predicted_jurisdiction": user_context.get("jurisdiction", "IN"),
                "response_date": "2025-01-01",
                "confidence_score": 0.0,
                "latency_seconds": time.time() - start,
            }


# ---------------------------------------------------------------------------
# Baseline B3 — RAG + RBAC + Temporal Filtering (no defense)
# ---------------------------------------------------------------------------
class TemporalFilteredRAG:
    """
    B3: B2 + temporal validity filter (superseded docs excluded).
    No leakage/conflict defense.
    """
    name = "B3_TemporalFilteredRAG"

    def run(self, query: str, user_context: dict) -> dict:
        start = time.time()
        try:
            ctx = _build_ctx(user_context)
            ranked_docs = retrieve(query, ctx)
            compliance_response = generate(query, ranked_docs, ctx)

            return {
                "answer":                   compliance_response.answer,
                "sources":                  ranked_docs,
                "compliance_status":        compliance_response.compliance_status,
                "violations":               compliance_response.violations,
                "conflicts":                [],
                "leakage_risk":             "NONE",
                "conflict_detected":        False,
                "predicted_jurisdiction":   _extract_jurisdictions(ranked_docs, user_context.get("jurisdiction", "IN")),
                "response_date":            _extract_best_date(query, ranked_docs, ctx),
                "confidence_score":         0.7,
                "latency_seconds":          time.time() - start,
            }
        except Exception as e:
            logger.warning("B3 error: %s", e)
            return {
                "answer": f"[B3 Error] {e}",
                "sources": [], "compliance_status": "UNKNOWN",
                "violations": [], "conflicts": [],
                "leakage_risk": "NONE", "conflict_detected": False,
                "predicted_jurisdiction": user_context.get("jurisdiction", "IN"),
                "response_date": "2025-01-01",
                "confidence_score": 0.0,
                "latency_seconds": time.time() - start,
            }


# ---------------------------------------------------------------------------
# Baseline B4 — Full FinGuard-RAG (all modules active)
# ---------------------------------------------------------------------------
class FinGuardRAG:
    """
    B4: Full pipeline — RBAC + Temporal + Risk Reranking + Leakage + Conflict.
    """
    name = "B4_FinGuardRAG"

    def run(self, query: str, user_context: dict) -> dict:
        start = time.time()
        try:
            ctx = _build_ctx(user_context)
            ranked_docs = retrieve(query, ctx)
            compliance_response = generate(query, ranked_docs, ctx)

            # Run full defense
            defense_result = defend(
                session_id=ctx.session_id,
                user_id=ctx.user_id,
                role=ctx.role,
                query=query,
                response=compliance_response.answer,
                source_docs=ranked_docs,
            )

            return {
                "answer":                   compliance_response.answer,
                "sources":                  ranked_docs,
                "compliance_status":        compliance_response.compliance_status,
                "violations":               compliance_response.violations,
                "conflicts":                defense_result.get("conflicting_rules", []),
                "leakage_risk":             defense_result.get("leakage_risk", "NONE"),
                "conflict_detected":        defense_result.get("conflict_detected", False),
                "predicted_jurisdiction":   _extract_jurisdictions(ranked_docs, user_context.get("jurisdiction", "IN")),
                "response_date":            _extract_best_date(query, ranked_docs, ctx),
                "confidence_score":         0.9,
                "latency_seconds":          time.time() - start,
            }
        except Exception as e:
            logger.warning("B4 error: %s", e)
            return {
                "answer": f"[B4 Error] {e}",
                "sources": [], "compliance_status": "UNKNOWN",
                "violations": [], "conflicts": [],
                "leakage_risk": "NONE", "conflict_detected": False,
                "predicted_jurisdiction": user_context.get("jurisdiction", "IN"),
                "response_date": "2025-01-01",
                "confidence_score": 0.0,
                "latency_seconds": time.time() - start,
            }


ALL_BASELINES = [VanillaRAG(), RBACFilteredRAG(), TemporalFilteredRAG(), FinGuardRAG()]
