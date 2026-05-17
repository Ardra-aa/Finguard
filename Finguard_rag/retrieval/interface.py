"""
Finguard_rag/retrieval/interface.py
Devna Thunnan — M1–M4: Public Retrieval Interface

The single function that ALL other modules (generation, agent, defense)
must call. Never import internals directly — always use retrieve().

Pipeline:
  1. Embed query (embedder.py)
  2. Time-versioned retrieval from ChromaDB (versioned_retriever.py)
  3. RBAC + jurisdiction post-filter (pre_filter.py)
  4. Risk-aware scoring & ranking (risk_scorer.py)
  5. Return top_k RankedDocument objects
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from typing import List
from datetime import date

from Finguard_rag.schemas.document_schema import (
    FinancialDocument,
    UserContext,
    RankedDocument,
)


def retrieve(
    query: str,
    user_context: UserContext,
    top_k: int = 5,
    mock_mode: bool = False,
) -> List[RankedDocument]:
    """
    Retrieve compliance-filtered, time-versioned, risk-ranked documents.

    Args:
        query:        User's compliance question (plain text).
        user_context: UserContext with role, jurisdiction, reference_date, session_id.
        top_k:        Maximum number of documents to return (default 5).
        mock_mode:    If True, return 3 deterministic dummy RankedDocuments instantly
                      (no ChromaDB or embedding calls — safe for unit testing).

    Returns:
        List[RankedDocument]: Up to top_k ranked, compliant document chunks.

    Raises:
        RuntimeError: If ChromaDB collection is empty (ingestor not run yet).

    Example:
        >>> from datetime import date
        >>> ctx = UserContext(
        ...     user_id='arjun@bharatfinserv.in',
        ...     role='junior_analyst',
        ...     jurisdiction='IN',
        ...     reference_date=date.today(),
        ...     session_id='sess_001',
        ... )
        >>> docs = retrieve('What are SEBI disclosure rules?', ctx, top_k=5)
        >>> print(f'Got {len(docs)} compliant documents')
    """
    # ------------------------------------------------------------------
    # MOCK MODE — deterministic stubs for development / unit tests
    # ------------------------------------------------------------------
    if mock_mode:
        dummy1 = FinancialDocument(
            doc_id='SEBI-LODR-2015-REG30',
            content='Regulation 30 requires timely disclosure of material events...',
            jurisdiction='IN',
            regulatory_scope='securities',
            valid_roles=['junior_analyst', 'senior_analyst', 'compliance_officer'],
            effective_date=date(2015, 9, 1),
            superseded_date=None,
            version='3.0',
            risk_level='LOW',
            risk_score=0.2,
            source_file='SEBI_LODR_2015.pdf',
        )
        dummy2 = FinancialDocument(
            doc_id='SEBI-MC-LODR-2023',
            content='Master Circular 2023 consolidates all LODR amendments...',
            jurisdiction='IN',
            regulatory_scope='securities',
            valid_roles=['junior_analyst', 'senior_analyst', 'compliance_officer'],
            effective_date=date(2023, 4, 1),
            superseded_date=None,
            version='1.0',
            risk_level='LOW',
            risk_score=0.15,
            source_file='SEBI_MasterCircular_LODR_2023.pdf',
        )
        dummy3 = FinancialDocument(
            doc_id='MCA-CA-2013-S133',
            content='Section 133 of Companies Act requires disclosure of board policies...',
            jurisdiction='IN',
            regulatory_scope='corporate',
            valid_roles=['compliance_officer', 'ceo', 'legal_counsel'],
            effective_date=date(2013, 4, 1),
            superseded_date=None,
            version='2.0',
            risk_level='MEDIUM',
            risk_score=0.5,
            source_file='Companies_Act_2013.pdf',
        )
        return [
            RankedDocument(document=dummy1, semantic_score=0.92, risk_score=0.20, final_score=0.584),
            RankedDocument(document=dummy2, semantic_score=0.88, risk_score=0.15, final_score=0.571),
            RankedDocument(document=dummy3, semantic_score=0.75, risk_score=0.50, final_score=0.375),
        ]

    # ------------------------------------------------------------------
    # LIVE PIPELINE
    # ------------------------------------------------------------------

    # Step 1: Embed the query
    from Finguard_rag.ingestion.embedder import embed_query
    query_embedding = embed_query(query)

    # Step 2: Time-versioned retrieval from ChromaDB
    # Fetch a larger candidate pool (top_k * 10) so filtering doesn't leave us short
    from Finguard_rag.retrieval.versioned_retriever import versioned_query
    n_candidates = max(top_k * 10, 50)
    candidates = versioned_query(
        query_embedding=query_embedding,
        user_context=user_context,
        n_candidates=n_candidates,
        top_k=n_candidates,   # don't truncate before RBAC filter
    )

    if not candidates:
        return []

    # Step 3: RBAC + jurisdiction post-filter
    from Finguard_rag.retrieval.pre_filter import post_filter
    filtered = post_filter(candidates, user_context)

    if not filtered:
        return []

    # Step 4: Risk-aware scoring and ranking
    from Finguard_rag.retrieval.risk_scorer import score_and_rank
    ranked = score_and_rank(filtered)

    # Step 5: Return top_k
    return ranked[:top_k]
