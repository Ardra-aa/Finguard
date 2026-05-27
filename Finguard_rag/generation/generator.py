"""
Finguard_rag/generation/generator.py
Amala P Ansalem — M5: LLM Generation Module

Accepts a list of RankedDocument objects from the retrieval layer, builds
a structured prompt (via prompt_builder), calls the LLM (via gemini_client),
and returns a raw answer string together with the source document list.

This is the implementation that ``generation/interface.py`` delegates to
when ``mock_mode=False``.

Pipeline:
    1. prompt_builder.build_prompt()  →  full prompt string
    2. gemini_client.call_llm()       →  raw LLM answer text
    3. Extract source documents from the ranked docs
    4. Return (answer_text, source_documents)

Compliance validation (M6) is NOT done here — it is applied in
interface.py after this module returns.
"""

import sys
import logging
from typing import List, Tuple
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Finguard_rag.schemas.document_schema import (
    FinancialDocument,
    RankedDocument,
    UserContext,
)
from Finguard_rag.generation.prompt_builder import build_prompt
from Finguard_rag.generation.gemini_client import call_llm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mock response for testing / development
# ---------------------------------------------------------------------------
_MOCK_ANSWER = (
    "Under SEBI LODR Regulation 30 (2015, as amended by Master Circular 2023), "
    "listed entities must disclose material events to the stock exchanges within "
    "24 hours of occurrence or within 30 minutes for certain events specified in "
    "Part A of Schedule III. The compliance officer is responsible for determining "
    "materiality and ensuring timely disclosure. "
    "[Source: SEBI-LODR-2015-REG30] [Source: SEBI-MC-LODR-2023]"
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_answer(
    query: str,
    docs: List[RankedDocument],
    user_context: UserContext,
    mock_mode: bool = False,
) -> Tuple[str, List[FinancialDocument]]:
    """
    Generate a raw LLM answer from retrieved documents.

    This function is the core of Module M5.  It does **not** perform
    compliance validation — that is M6's responsibility and is applied
    by ``interface.generate()`` after this function returns.

    Args:
        query:        The user's compliance question (plain text).
        docs:         Ranked, compliance-filtered documents from retrieval.
        user_context: Current user metadata (role, jurisdiction, etc.).
        mock_mode:    If True, skip the LLM call and return a canned answer.

    Returns:
        A ``(answer_text, source_documents)`` tuple where:
        - ``answer_text`` is the raw string produced by the LLM.
        - ``source_documents`` is the list of FinancialDocument objects
          that were included in the prompt context.

    Raises:
        RuntimeError: If both Gemini and Groq fail (propagated from
            ``gemini_client.call_llm``).
    """
    # Collect source documents from the ranked results
    source_documents: List[FinancialDocument] = [
        ranked.document for ranked in docs
    ]

    # ------------------------------------------------------------------ #
    # Mock mode — instant return, no API calls
    # ------------------------------------------------------------------ #
    if mock_mode:
        logger.info("generator.generate_answer — mock_mode=True")
        return _MOCK_ANSWER, source_documents

    # ------------------------------------------------------------------ #
    # Live mode
    # ------------------------------------------------------------------ #
    if not docs:
        no_context_answer = (
            "I could not find any relevant, compliant documents for your query. "
            "This may be because:\n"
            "1. Your role does not have access to the relevant documents.\n"
            "2. The documents have been superseded and are no longer current.\n"
            "3. The query falls outside the available regulatory corpus.\n\n"
            "Please refine your query or contact the compliance team for assistance."
        )
        return no_context_answer, []

    # Step 1: Build the structured prompt
    prompt = build_prompt(query, docs, user_context)
    logger.info(
        "Prompt built — %d source docs, ~%d chars",
        len(docs),
        len(prompt),
    )

    # Step 2: Call the LLM
    answer_text = call_llm(prompt, mock_mode=False)
    logger.info(
        "LLM response received — %d chars",
        len(answer_text),
    )

    return answer_text, source_documents
