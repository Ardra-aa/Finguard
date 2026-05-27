# finguard_rag/schemas/response_schema.py
# ──────────────────────────────────────────────────────────────────────────────
# Response-related schemas for the FinGuard-RAG pipeline.
#
# These schemas are re-exported from document_schema.py for clarity.
# Any module that only needs response types can import from this file:
#   from finguard_rag.schemas.response_schema import ComplianceResponse, ...
#
# The canonical definitions live in document_schema.py (Section 9 of the
# Master Implementation Document) so that all schemas remain in one place.
# ──────────────────────────────────────────────────────────────────────────────

from Finguard_rag.schemas.document_schema import (
    ComplianceResponse,
    DefenseResult,
    AgentResponse,
    RankedDocument,
)

__all__ = [
    "ComplianceResponse",
    "DefenseResult",
    "AgentResponse",
    "RankedDocument",
]
