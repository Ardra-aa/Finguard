"""
M10 — Baseline Systems
Four baselines from vanilla RAG up to full FinGuard-RAG.
Each baseline is a callable that takes (query, user_context) → dict.
They are used for ablation comparison in the evaluation harness.
"""

from __future__ import annotations
from typing import List
import time


# ---------------------------------------------------------------------------
# Baseline B1 — Vanilla RAG (no compliance, no defense)
# ---------------------------------------------------------------------------
class VanillaRAG:
    """
    B1: Retrieve top-k chunks by semantic similarity, generate with no filters.
    Stub: returns mock response; wire in real retrieval/generation if available.
    """
    name = "B1_VanillaRAG"

    def run(self, query: str, user_context: dict) -> dict:
        start = time.time()
        # In integration: call retrieval.interface + generation.interface directly
        response = {
            "answer":                   f"[B1 Vanilla] Answer for: {query}",
            "sources":                  [],
            "compliance_status":        "UNKNOWN",
            "violations":               [],
            "conflicts":                [],
            "leakage_risk":             "NONE",
            "conflict_detected":        False,
            "predicted_jurisdiction":   user_context.get("jurisdiction", "IN"),
            "confidence_score":         0.5,
            "latency_seconds":          time.time() - start,
        }
        return response


# ---------------------------------------------------------------------------
# Baseline B2 — RAG + Role-Based Access Control only
# ---------------------------------------------------------------------------
class RBACFilteredRAG:
    """
    B2: Vanilla RAG + role-filtered retrieval (no temporal, no leakage, no conflict).
    """
    name = "B2_RBACFilteredRAG"

    def run(self, query: str, user_context: dict) -> dict:
        start = time.time()
        role = user_context.get("role", "junior_analyst")
        response = {
            "answer":                   f"[B2 RBAC] Role={role} — Answer for: {query}",
            "sources":                  [],
            "compliance_status":        "PASS",
            "violations":               [],
            "conflicts":                [],
            "leakage_risk":             "NONE",
            "conflict_detected":        False,
            "predicted_jurisdiction":   user_context.get("jurisdiction", "IN"),
            "confidence_score":         0.6,
            "latency_seconds":          time.time() - start,
        }
        return response


# ---------------------------------------------------------------------------
# Baseline B3 — RAG + RBAC + Temporal Filtering
# ---------------------------------------------------------------------------
class TemporalFilteredRAG:
    """
    B3: B2 + temporal validity filter (superseded docs excluded).
    """
    name = "B3_TemporalFilteredRAG"

    def run(self, query: str, user_context: dict) -> dict:
        start = time.time()
        response = {
            "answer":                   f"[B3 Temporal] Answer for: {query}",
            "sources":                  [],
            "compliance_status":        "PASS",
            "violations":               [],
            "conflicts":                [],
            "leakage_risk":             "NONE",
            "conflict_detected":        False,
            "predicted_jurisdiction":   user_context.get("jurisdiction", "IN"),
            "confidence_score":         0.7,
            "latency_seconds":          time.time() - start,
        }
        return response


# ---------------------------------------------------------------------------
# Baseline B4 — Full FinGuard-RAG (all modules active)
# ---------------------------------------------------------------------------
class FinGuardRAG:
    """
    B4: Full pipeline — RBAC + Temporal + Risk Reranking + Leakage + Conflict.
    In integration: wire all module interfaces here.
    """
    name = "B4_FinGuardRAG"

    def run(self, query: str, user_context: dict) -> dict:
        start = time.time()
        response = {
            "answer":                   f"[B4 FinGuard] Answer for: {query}",
            "sources":                  [],
            "compliance_status":        "PASS",
            "violations":               [],
            "conflicts":                [],
            "leakage_risk":             "NONE",
            "conflict_detected":        False,
            "predicted_jurisdiction":   user_context.get("jurisdiction", "IN"),
            "confidence_score":         0.9,
            "latency_seconds":          time.time() - start,
        }
        return response


ALL_BASELINES = [VanillaRAG(), RBACFilteredRAG(), TemporalFilteredRAG(), FinGuardRAG()]
