"""
M11 — FastAPI Route Handlers
4 endpoints:
    POST /query                        — main RAG query (with mock-mode defence pipeline)
    GET  /health                       — liveness check
    GET  /session/{session_id}/leakage — M8 leakage report for a session
    GET  /admin/sessions               — admin audit view of all sessions
"""

from __future__ import annotations
from datetime import date as dt
from typing import List

from fastapi import APIRouter, HTTPException

from .models import (
    QueryRequest, QueryResponse, HealthResponse,
    LeakageReport, SessionSummary,
)
from ..defense.interface import defend
from ..defense.session_tracker import SessionTracker

router   = APIRouter()
_tracker = SessionTracker()


# ---------------------------------------------------------------------------
# POST /query
# ---------------------------------------------------------------------------
@router.post("/query", response_model=QueryResponse)
async def query_endpoint(req: QueryRequest):
    """
    Main query endpoint.  Wires the defence module (M8 + M9) around a stub
    retrieval + generation step.  Replace the stub sections with real calls
    once retrieval.interface and agent.interface are available.
    """
    ref_date = req.reference_date or dt.today()

    # ── Step 1: Retrieval stub ────────────────────────────────────────────
    # Replace with:  from ..retrieval.interface import retrieve
    #                ranked_docs = retrieve(req.query, user_ctx, top_k=5)
    mock_ranked_docs = []          # List[RankedDocument]

    # ── Step 2: Generation stub ───────────────────────────────────────────
    # Replace with:  from ..agent.interface import agent_run
    #                agent_resp = agent_run(req.query, user_ctx)
    #                mock_answer = agent_resp.final_response.answer
    mock_answer = (
        f"Based on applicable regulations for jurisdiction {req.jurisdiction}, "
        f"here is the compliance guidance for your query: \"{req.query}\". "
        f"Please refer to SEBI LODR 2015, RBI Master Directions, and Companies Act 2013 "
        f"for the full regulatory provisions relevant to your role ({req.role})."
    )

    # ── Step 3: Build UserContext ─────────────────────────────────────────
    from ..schemas.document_schema import UserContext
    user_ctx = UserContext(
        user_id        = req.user_id,
        role           = req.role,
        jurisdiction   = req.jurisdiction,
        reference_date = ref_date,
        session_id     = req.session_id,
    )

    # ── Step 4: Defence (M8 leakage + M9 conflict) ───────────────────────
    defense_result = defend(
        session_id   = req.session_id,
        user_id      = req.user_id,
        role         = req.role,
        query        = req.query,
        response     = mock_answer,
        source_docs  = mock_ranked_docs,   # [] until retrieval is wired
        user_context = user_ctx,
        mock_mode    = req.mock_mode,
    )

    # Block query if HIGH leakage risk detected
    if defense_result["leakage_risk"] == "HIGH":
        raise HTTPException(
            status_code = 403,
            detail = {
                "error":   "Query blocked: high role-inference leakage risk detected.",
                "details": defense_result["leakage_details"],
            },
        )

    # ── Step 5: Return structured response ────────────────────────────────
    return QueryResponse(
        answer                       = mock_answer,
        sources                      = [],      # populated when retrieval is wired
        compliance_status            = "WARNING" if defense_result["conflict_detected"] else "PASS",
        violations                   = [],
        conflicts                    = defense_result["conflicting_rules"],
        leakage_risk                 = defense_result["leakage_risk"],
        leakage_details              = defense_result["leakage_details"],
        conflict_detected            = defense_result["conflict_detected"],
        conflicting_rules            = defense_result["conflicting_rules"],
        conservative_recommendation  = defense_result["conservative_recommendation"],
        confidence_score             = 0.85,
        agent_trace                  = None,
    )


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


# ---------------------------------------------------------------------------
# GET /session/{session_id}/leakage
# ---------------------------------------------------------------------------
@router.get("/session/{session_id}/leakage", response_model=LeakageReport)
async def get_leakage_report(session_id: str):
    report = _tracker.get_report(session_id)
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return LeakageReport(**report)


# ---------------------------------------------------------------------------
# GET /admin/sessions
# ---------------------------------------------------------------------------
@router.get("/admin/sessions", response_model=List[SessionSummary])
async def get_all_sessions():
    return [SessionSummary(**s) for s in _tracker.get_all_sessions()]
