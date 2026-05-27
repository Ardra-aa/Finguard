"""
Finguard_rag/generation/prompt_builder.py
Amala P Ansalem — M5: Structured Prompt Builder

Assembles the full prompt that is sent to the LLM.  The prompt has three
sections:

    1. SYSTEM — persona, output format, citation instructions
    2. CONTEXT — retrieved document chunks (trimmed to fit token budget)
    3. QUERY — the user's question plus role/jurisdiction metadata

Token budget management:
    The free-tier Gemini 1.5 Flash accepts up to ~1 M tokens, but the
    implementation plan caps the *input* at 8 192 tokens to keep responses
    fast and quota-friendly.  This module estimates token counts using a
    simple 4-characters-per-token heuristic and trims the lowest-ranked
    context chunks first when the budget is exceeded.
"""

import sys
import logging
from typing import List
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Finguard_rag.schemas.document_schema import RankedDocument, UserContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_INPUT_TOKENS = 8192          # token budget from implementation.md
CHARS_PER_TOKEN  = 4             # rough estimate for English text

SYSTEM_PROMPT = """\
You are **FinGuard-RAG**, a senior compliance advisor for BharatFinServ Ltd.,
a fictional Indian financial MNC listed on BSE and NSE.

Your job is to answer financial compliance questions **only** based on the
CONTEXT DOCUMENTS provided below.  Follow these rules strictly:

1. **Citation required** — Every factual claim must end with a citation in
   the format:  [Source: <doc_id>]
   Example: "...must be disclosed within 24 hours [Source: SEBI-LODR-2015-REG30]."

2. **Jurisdiction awareness** — If the user's jurisdiction is specified,
   frame the answer under that jurisdiction's regulations only.

3. **Temporal awareness** — Only cite documents whose effective_date <=
   today and that are NOT superseded (superseded_date is null or in the
   future).  If a document is superseded, note this explicitly.

4. **Do NOT hallucinate** — If the provided context documents do not
   contain enough information, say so.  Never invent regulatory provisions.

5. **Professional tone** — Use formal, advisory language appropriate for
   a compliance officer or CFO audience.

6. **Structured answer** — Use numbered points or bullet points for
   multi-part answers.  Keep the answer concise (300–500 words).
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _estimate_tokens(text: str) -> int:
    """Rough token count based on character length."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def _format_context_chunk(idx: int, doc: RankedDocument) -> str:
    """
    Format a single RankedDocument as a numbered context block.

    Returns a string like:

        --- CONTEXT DOCUMENT 1 ---
        doc_id: SEBI-LODR-2015-REG30
        jurisdiction: IN | effective: 2015-09-01 | version: 3.0
        risk_level: LOW | relevance_score: 0.92
        CONTENT:
        <chunk text>
    """
    d = doc.document
    return (
        f"--- CONTEXT DOCUMENT {idx} ---\n"
        f"doc_id: {d.doc_id}\n"
        f"jurisdiction: {d.jurisdiction} | effective: {d.effective_date} | "
        f"version: {d.version}\n"
        f"risk_level: {d.risk_level} | relevance_score: {doc.semantic_score:.2f}\n"
        f"CONTENT:\n{d.content}\n"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_prompt(
    query: str,
    docs: List[RankedDocument],
    user_context: UserContext,
) -> str:
    """
    Assemble the full LLM prompt from system instructions, context
    documents, and the user query.

    If the combined prompt exceeds ``MAX_INPUT_TOKENS`` the lowest-ranked
    context documents are dropped one-by-one until it fits.

    Args:
        query:        The user's compliance question.
        docs:         Retrieved & ranked documents (highest score first).
        user_context: Current user metadata (role, jurisdiction, etc.).

    Returns:
        A single prompt string ready to send to :func:`gemini_client.call_llm`.
    """
    # ------------------------------------------------------------------ #
    # 1. Build the fixed (non-context) parts of the prompt
    # ------------------------------------------------------------------ #
    user_meta = (
        f"USER METADATA:\n"
        f"  role: {user_context.role}\n"
        f"  jurisdiction: {user_context.jurisdiction}\n"
        f"  reference_date: {user_context.reference_date}\n"
    )

    query_section = (
        f"USER QUERY:\n{query}\n\n"
        f"Provide a comprehensive, well-cited answer following the rules above."
    )

    fixed_text = f"{SYSTEM_PROMPT}\n\n{user_meta}\n"
    fixed_tokens = _estimate_tokens(fixed_text)

    query_tokens = _estimate_tokens(query_section)

    budget_for_context = MAX_INPUT_TOKENS - fixed_tokens - query_tokens
    if budget_for_context < 100:
        logger.warning(
            "Token budget leaves only %d tokens for context — query may be "
            "too long",
            budget_for_context,
        )
        budget_for_context = 100  # allow at least a small snippet

    # ------------------------------------------------------------------ #
    # 2. Fill the context section, trimming from the tail if needed
    # ------------------------------------------------------------------ #
    context_blocks: List[str] = []
    used_tokens = 0

    for idx, doc in enumerate(docs, start=1):
        block = _format_context_chunk(idx, doc)
        block_tokens = _estimate_tokens(block)

        if used_tokens + block_tokens > budget_for_context:
            logger.info(
                "Token budget reached after %d/%d context docs — trimming.",
                idx - 1,
                len(docs),
            )
            break

        context_blocks.append(block)
        used_tokens += block_tokens

    if not context_blocks:
        context_section = (
            "CONTEXT DOCUMENTS:\n"
            "(No relevant documents were retrieved for this query.)\n"
        )
    else:
        context_section = "CONTEXT DOCUMENTS:\n\n" + "\n".join(context_blocks)

    # ------------------------------------------------------------------ #
    # 3. Assemble the full prompt
    # ------------------------------------------------------------------ #
    full_prompt = f"{fixed_text}{context_section}\n\n{query_section}"

    total_tokens = _estimate_tokens(full_prompt)
    logger.info(
        "Prompt assembled — %d context docs, ~%d tokens (budget: %d)",
        len(context_blocks),
        total_tokens,
        MAX_INPUT_TOKENS,
    )

    return full_prompt
