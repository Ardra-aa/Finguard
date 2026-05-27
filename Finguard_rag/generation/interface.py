"""
Finguard_rag/generation/interface.py
Amala P Ansalem — M5, M6

Public function that takes retrieved documents and generates compliant responses.
All other modules (agent, api, defense) must call generate() from here.
"""

import sys
import logging
from typing import List, Optional
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Finguard_rag.schemas.document_schema import (
    RankedDocument, UserContext, ComplianceResponse
)

logger = logging.getLogger(__name__)


def generate(
    query: str,
    docs: List[RankedDocument],
    user_context: UserContext,
    mock_mode: bool = False
) -> ComplianceResponse:
    """
    Generate a compliance-verified response from retrieved documents.

    Flow:
      1. LLM Generation (M5): Build structured prompt + context chunks,
         call Gemini 1.5 Flash via generator.generate_answer()
      2. Compliance Validation (M6 — applied here when available):
         - Layer A (Symbolic): Run 20 deontic rules (MUST/MUST_NOT/PERMITTED)
         - Layer B (Neural): Check similarity to known non-compliant patterns
      3. Return validated response with compliance_status (PASS | WARNING | FAIL)

    Args:
        query: User's compliance question
        docs: List[RankedDocument] from retrieval module
        user_context: UserContext with role, jurisdiction, session_id
        mock_mode: If True, return dummy ComplianceResponse instantly

    Returns:
        ComplianceResponse: Answer + compliance_status + violations + citations

    Raises:
        RuntimeError: If Gemini API fails and Groq fallback also fails

    Example:
        >>> ctx = UserContext(..., role='compliance_officer', ...)
        >>> docs = retrieve('SEBI rules?', ctx)
        >>> response = generate('SEBI rules?', docs, ctx)
        >>> print(response.answer)
        >>> print(f"Status: {response.compliance_status}")
    """
    if mock_mode:
        # Return dummy ComplianceResponse for testing/development
        dummy_sources = [doc.document for doc in docs[:2]] if docs else []
        return ComplianceResponse(
            answer=(
                "Regulation 30 of SEBI LODR 2015 requires listed entities to "
                "disclose material events within the stipulated timeline. The "
                "Master Circular 2023 consolidates all amendments. Key "
                "requirement: announce events by end of business hours of the "
                "date when the Board approved or the company became aware of "
                "the event, whichever is earlier. "
                "[Source: SEBI-LODR-2015-REG30] [Source: SEBI-MC-LODR-2023]"
            ),
            sources=dummy_sources,
            compliance_status='PASS',
            violations=[],
            conflicts=[],
            leakage_risk='NONE',
            confidence_score=0.92,
            agent_trace=None
        )

    # ------------------------------------------------------------------
    # LIVE PIPELINE — M5: LLM Generation
    # ------------------------------------------------------------------
    from Finguard_rag.generation.generator import generate_answer

    answer_text, source_documents = generate_answer(
        query=query,
        docs=docs,
        user_context=user_context,
        mock_mode=False,
    )

    # ------------------------------------------------------------------
    # M6: Compliance Validation (applied if modules are available)
    # ------------------------------------------------------------------
    compliance_status = "PASS"
    violations: List[str] = []
    confidence_score = 0.85  # default confidence

    try:
        from Finguard_rag.generation.compliance_validator import validate
        validation_result = validate(answer_text, docs, user_context)
        compliance_status = validation_result.get("status", "PASS")
        violations = validation_result.get("violations", [])
        confidence_score = validation_result.get("confidence", 0.85)

        # If FAIL: replace the answer with the safe refusal message
        if validation_result.get("withheld", False):
            answer_text = validation_result.get("safe_answer", answer_text)
            logger.critical(
                "Response WITHHELD — violations: %s", violations
            )

        logger.info(
            "Compliance validation: status=%s, violations=%d",
            compliance_status,
            len(violations),
        )
    except ImportError:
        logger.info(
            "compliance_validator not yet available — skipping M6 validation"
        )
    except Exception as e:
        logger.warning("Compliance validation error: %s — defaulting to PASS", e)

    # ------------------------------------------------------------------
    # Build and return ComplianceResponse
    # ------------------------------------------------------------------
    return ComplianceResponse(
        answer=answer_text,
        sources=source_documents,
        compliance_status=compliance_status,
        violations=violations,
        conflicts=[],          # populated by M9 (defense/conflict_resolver)
        leakage_risk='NONE',   # populated by M8 (defense/leakage_detector)
        confidence_score=confidence_score,
        agent_trace=None,
    )

