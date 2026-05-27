"""
Finguard_rag/agent/tool_registry.py
Amala P Ansalem — M7: LangChain Tool Registry

Wraps all FinGuard pipeline functions as LangChain-compatible Tool objects.
These tools are used by the ReAct agent in finguard_agent.py.

6 tools (from Section 5.1 of implementation.md):
    1. retrieve_compliant_docs  →  retrieval/interface.retrieve()
    2. check_compliance_rules   →  generation/rule_engine.evaluate_rules()
    3. detect_jurisdiction_conflict  →  defense/interface.defend() (conflict part)
    4. scan_leakage_risk        →  defense/interface.defend() (leakage part)
    5. explain_regulation       →  retrieve() + generate()
    6. get_document_history     →  retrieve() with historical date

Each tool accepts a single string input (LangChain convention) and returns
a string output.  The user_context is injected via closure at registration
time so the agent doesn't need to pass it explicitly.
"""

import sys
import json
import logging
from datetime import date
from typing import List, Callable
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Finguard_rag.schemas.document_schema import UserContext, RankedDocument

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: format ranked docs as readable text for the agent
# ---------------------------------------------------------------------------
def _format_docs(docs: List[RankedDocument]) -> str:
    """Format a list of RankedDocument objects as readable text."""
    if not docs:
        return "No documents retrieved."
    lines = []
    for i, rd in enumerate(docs, 1):
        d = rd.document
        lines.append(
            f"[{i}] doc_id={d.doc_id} | jurisdiction={d.jurisdiction} | "
            f"effective={d.effective_date} | score={rd.final_score:.3f}\n"
            f"    {d.content[:200]}..."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool factory functions — each returns a callable(str) -> str
# ---------------------------------------------------------------------------

def _make_retrieve_compliant_docs(
    user_context: UserContext,
    mock_mode: bool = False,
) -> Callable[[str], str]:
    """
    Tool 1: retrieve_compliant_docs
    Policy-aware + time-versioned retrieval for a sub-query.
    Maps to Stages 1–3 of the pipeline.
    """
    def _run(query: str) -> str:
        from Finguard_rag.retrieval.interface import retrieve
        docs = retrieve(
            query=query,
            user_context=user_context,
            top_k=5,
            mock_mode=mock_mode,
        )
        logger.info("retrieve_compliant_docs: %d docs for '%s'", len(docs), query[:60])
        return _format_docs(docs)
    return _run


def _make_check_compliance_rules(
    mock_mode: bool = False,
) -> Callable[[str], str]:
    """
    Tool 2: check_compliance_rules
    Run the symbolic deontic rule engine against a statement.
    Maps to Stage 5 (symbolic layer).
    """
    def _run(statement: str) -> str:
        if mock_mode:
            return "PASS — No violations detected (mock mode)."
        from Finguard_rag.generation.rule_engine import evaluate_rules
        status, violations = evaluate_rules(statement)
        if violations:
            return f"{status} — Violations: {', '.join(violations)}"
        return f"{status} — No violations detected."
    return _run


def _make_detect_jurisdiction_conflict(
    user_context: UserContext,
    mock_mode: bool = False,
) -> Callable[[str], str]:
    """
    Tool 3: detect_jurisdiction_conflict
    Check retrieved documents for conflicting legal regimes.
    Maps to Stage 6 (defense/conflict_resolver).

    Input: comma-separated doc_ids or a description of docs to check.
    """
    def _run(input_text: str) -> str:
        if mock_mode:
            return (
                "No jurisdiction conflicts detected (mock mode). "
                "All documents are from the same legal regime."
            )

        # Build minimal RankedDocument stubs for the defense interface
        from Finguard_rag.schemas.document_schema import FinancialDocument
        doc_ids = [s.strip() for s in input_text.split(",") if s.strip()]

        stub_docs = []
        for doc_id in doc_ids:
            stub = RankedDocument(
                document=FinancialDocument(
                    doc_id=doc_id,
                    content=f"Content for {doc_id}",
                    jurisdiction="IN",
                    regulatory_scope="securities",
                    valid_roles=["compliance_officer"],
                    effective_date=date(2023, 1, 1),
                ),
                semantic_score=0.8,
                risk_score=0.2,
                final_score=0.7,
            )
            stub_docs.append(stub)

        try:
            from Finguard_rag.defense.interface import defend
            result = defend(
                session_id=user_context.session_id,
                user_id=user_context.user_id,
                role=user_context.role,
                query=input_text,
                response="",
                source_docs=stub_docs,
                user_context=user_context,
                mock_mode=False,
            )
            if result["conflict_detected"]:
                rules = ", ".join(result["conflicting_rules"])
                return (
                    f"CONFLICT DETECTED: {rules}\n"
                    f"Recommendation: {result['conservative_recommendation']}"
                )
            return "No jurisdiction conflicts detected."
        except Exception as e:
            logger.warning("Conflict detection error: %s", e)
            return f"Conflict detection unavailable: {e}"

    return _run


def _make_scan_leakage_risk(
    user_context: UserContext,
    mock_mode: bool = False,
) -> Callable[[str], str]:
    """
    Tool 4: scan_leakage_risk
    Evaluate session query history for inference leakage.
    Maps to Stage 6 (defense/leakage_detector).
    """
    def _run(query: str) -> str:
        if mock_mode:
            return "Leakage risk: NONE (mock mode). Session history is clean."

        try:
            from Finguard_rag.defense.interface import defend
            # Use empty docs — we only care about leakage here
            result = defend(
                session_id=user_context.session_id,
                user_id=user_context.user_id,
                role=user_context.role,
                query=query,
                response="",
                source_docs=[],
                user_context=user_context,
                mock_mode=False,
            )
            risk = result["leakage_risk"]
            details = "; ".join(result["leakage_details"]) or "none"
            return f"Leakage risk: {risk}. Details: {details}"
        except Exception as e:
            logger.warning("Leakage scan error: %s", e)
            return f"Leakage scan unavailable: {e}"

    return _run


def _make_explain_regulation(
    user_context: UserContext,
    mock_mode: bool = False,
) -> Callable[[str], str]:
    """
    Tool 5: explain_regulation
    Retrieve and summarise a specific named regulation.
    Maps to Stages 1–4 (retrieve + generate).
    """
    def _run(regulation_name: str) -> str:
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate

        explain_query = f"Explain the key provisions of {regulation_name}"
        docs = retrieve(
            query=explain_query,
            user_context=user_context,
            top_k=3,
            mock_mode=mock_mode,
        )
        if not docs:
            return f"No documents found for regulation: {regulation_name}"

        response = generate(
            query=explain_query,
            docs=docs,
            user_context=user_context,
            mock_mode=mock_mode,
        )
        return response.answer

    return _run


def _make_get_document_history(
    user_context: UserContext,
    mock_mode: bool = False,
) -> Callable[[str], str]:
    """
    Tool 6: get_document_history
    Retrieve all versions of a regulatory document, including superseded.
    Maps to Stage 2 (time-versioned retrieval).
    """
    def _run(doc_name: str) -> str:
        from Finguard_rag.retrieval.interface import retrieve

        # Use a very early reference date to capture old versions
        historical_context = UserContext(
            user_id=user_context.user_id,
            role=user_context.role,
            jurisdiction=user_context.jurisdiction,
            reference_date=date(2010, 1, 1),  # far in the past
            session_id=user_context.session_id,
        )

        history_query = f"All versions of {doc_name}"
        docs = retrieve(
            query=history_query,
            user_context=historical_context,
            top_k=10,
            mock_mode=mock_mode,
        )
        if not docs:
            return f"No version history found for: {doc_name}"

        lines = [f"Version history for '{doc_name}':"]
        for i, rd in enumerate(docs, 1):
            d = rd.document
            status = "CURRENT" if d.superseded_date is None else f"SUPERSEDED ({d.superseded_date})"
            lines.append(
                f"  [{i}] {d.doc_id} v{d.version} | "
                f"effective: {d.effective_date} | {status}"
            )
        return "\n".join(lines)

    return _run


# ---------------------------------------------------------------------------
# Public API — build the full tool list for a given user context
# ---------------------------------------------------------------------------
def build_tools(
    user_context: UserContext,
    mock_mode: bool = False,
) -> list:
    """
    Build and return the list of 6 LangChain Tool objects for the agent.

    Each tool wraps a pipeline function with the given user_context
    bound via closure.

    Args:
        user_context: Current user metadata (role, jurisdiction, etc.).
        mock_mode:    If True, all tools return mock responses.

    Returns:
        List of LangChain Tool objects ready for AgentExecutor.
    """
    from langchain.tools import Tool

    tools = [
        Tool(
            name="retrieve_compliant_docs",
            func=_make_retrieve_compliant_docs(user_context, mock_mode),
            description=(
                "Policy-aware, time-versioned retrieval for a compliance sub-query. "
                "Input: a natural language query string about a specific regulation or topic. "
                "Output: ranked list of compliant document chunks with doc_ids and scores."
            ),
        ),
        Tool(
            name="check_compliance_rules",
            func=_make_check_compliance_rules(mock_mode),
            description=(
                "Run the symbolic deontic rule engine (20 SEBI/RBI/MCA/Ind AS rules) "
                "against a statement. Input: a statement to validate. "
                "Output: PASS/WARNING/FAIL with violated rule IDs."
            ),
        ),
        Tool(
            name="detect_jurisdiction_conflict",
            func=_make_detect_jurisdiction_conflict(user_context, mock_mode),
            description=(
                "Check if retrieved documents contain conflicting legal regimes "
                "(e.g., SEBI vs Companies Act, Ind AS vs IFRS). "
                "Input: comma-separated doc_ids to compare. "
                "Output: conflict status and conservative recommendation."
            ),
        ),
        Tool(
            name="scan_leakage_risk",
            func=_make_scan_leakage_risk(user_context, mock_mode),
            description=(
                "Evaluate the current session's query history for role-inference "
                "leakage attacks. Input: the current query text. "
                "Output: leakage risk level (NONE/LOW/HIGH) and details."
            ),
        ),
        Tool(
            name="explain_regulation",
            func=_make_explain_regulation(user_context, mock_mode),
            description=(
                "Fetch and summarise a specific named regulation. "
                "Input: the name of the regulation (e.g., 'SEBI LODR Reg 30'). "
                "Output: a concise summary of the regulation's key provisions."
            ),
        ),
        Tool(
            name="get_document_history",
            func=_make_get_document_history(user_context, mock_mode),
            description=(
                "Retrieve all versions of a regulatory document, including "
                "superseded ones. Input: document name or doc_id. "
                "Output: version timeline with effective dates and status."
            ),
        ),
    ]

    logger.info("Built %d agent tools for role=%s", len(tools), user_context.role)
    return tools
