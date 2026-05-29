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

4. **Use available context fully** — Synthesize a comprehensive answer
   from ALL provided context documents.  If some aspects of the query
   are not fully covered, answer what you can from the context and note
   any gaps.  Never invent regulatory provisions not found in the context,
   but DO provide substantive answers from the documents you have.

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

    Injects actual document content from ranked_docs into the prompt
    so the LLM can synthesize real answers with citations.

    Args:
        query:        The user's compliance question.
        docs:         Retrieved & ranked documents (highest score first).
        user_context: Current user metadata (role, jurisdiction, etc.).

    Returns:
        A single prompt string ready to send to :func:`gemini_client.call_llm`.
    """
    # ------------------------------------------------------------------ #
    # 1. Build context from real document chunks
    # ------------------------------------------------------------------ #
    context_sections = []
    for i, doc in enumerate(docs[:5]):  # top 5 docs
        content = doc.document.content or ""
        if content:
            context_sections.append(
                f"[Source {i+1}: {doc.document.doc_id}]\n{content[:1500]}"
            )

    if not context_sections:
        context_block = "No relevant documents found in the corpus."
    else:
        context_block = "\n\n".join(context_sections)

    # ------------------------------------------------------------------ #
    # 2. Assemble the full prompt
    # ------------------------------------------------------------------ #
    prompt = f"""You are FinGuard, a financial compliance assistant for BharatFinServ Ltd. You answer questions strictly based on the provided regulatory documents.

USER ROLE: {user_context.role}
JURISDICTION: {user_context.jurisdiction}

RETRIEVED REGULATORY CONTEXT:
{context_block}

INSTRUCTIONS:
1. Answer ONLY using information from the retrieved context above.
2. Write a complete, structured answer in clear paragraphs — not bullet points, not "please refer to document X".
3. Cite sources inline as [Source: doc_id] after each fact.
4. If the context does not contain enough information to answer, say: "The available regulatory documents do not contain sufficient information on this topic for your role and jurisdiction."
5. Do NOT say "please refer to" or "consult the document" — extract and explain the actual content.
6. Tailor the answer to the user's role ({user_context.role}) — a junior_analyst gets a simpler explanation than a cfo.

QUERY: {query}

ANSWER:"""

    total_tokens = _estimate_tokens(prompt)
    logger.info(
        "Prompt assembled — %d context docs, ~%d tokens (budget: %d)",
        len(context_sections),
        total_tokens,
        MAX_INPUT_TOKENS,
    )

    return prompt
