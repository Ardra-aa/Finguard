"""
tests/integration/test_pipeline_mock.py
=======================================
Integration tests for the FinGuard-RAG pipeline in mock_mode.

These tests verify the Section 9 Integration Contract (implementation.md):
  - retrieve()  → List[RankedDocument]
  - generate()  → ComplianceResponse
  - agent_run() → AgentResponse
  - defend()    → dict matching DefenseResult fields

All tests run with mock_mode=True — no API keys, no ChromaDB, no GPU needed.
This is the gate described in Section 10.3:
  "Before any PR merge to dev: run pytest tests/integration/ — all tests must pass."
"""

import sys
from pathlib import Path
from datetime import date

import pytest

# Ensure repo root is importable
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Finguard_rag.schemas.document_schema import (
    FinancialDocument,
    UserContext,
    RankedDocument,
    ComplianceResponse,
    AgentResponse,
    DefenseResult,
)

# ── Shared Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def junior_analyst_ctx():
    """Junior analyst — most restricted role (IN only)."""
    return UserContext(
        user_id='arjun.kumar@bharatfinserv.in',
        role='junior_analyst',
        jurisdiction='IN',
        reference_date=date.today(),
        session_id='test-session-001',
    )


@pytest.fixture
def ceo_ctx():
    """CEO — broadest role (all jurisdictions)."""
    return UserContext(
        user_id='rahul.sharma@bharatfinserv.in',
        role='ceo',
        jurisdiction='IN',
        reference_date=date.today(),
        session_id='test-session-002',
    )


@pytest.fixture
def compliance_officer_ctx():
    """Compliance officer — broad access, compliance-focused."""
    return UserContext(
        user_id='ananya.iyer@bharatfinserv.in',
        role='compliance_officer',
        jurisdiction='IN',
        reference_date=date.today(),
        session_id='test-session-003',
    )


# ============================================================================
# TEST GROUP 1: M1–M4 — Retrieval Interface (retrieve)
# ============================================================================

class TestRetrievalInterface:
    """Verify retrieve() mock_mode contract (Member 1 — Devna)."""

    def test_mock_returns_three_ranked_documents(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        results = retrieve('KYC requirements', junior_analyst_ctx, mock_mode=True)
        assert len(results) == 3, f"Expected 3 mock results, got {len(results)}"

    def test_mock_returns_ranked_document_instances(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        results = retrieve('KYC requirements', junior_analyst_ctx, mock_mode=True)
        for r in results:
            assert isinstance(r, RankedDocument), f"Expected RankedDocument, got {type(r)}"

    def test_mock_documents_contain_financial_document(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        results = retrieve('KYC requirements', junior_analyst_ctx, mock_mode=True)
        for r in results:
            assert isinstance(r.document, FinancialDocument)

    def test_mock_results_sorted_descending_by_final_score(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        results = retrieve('KYC requirements', junior_analyst_ctx, mock_mode=True)
        for i in range(len(results) - 1):
            assert results[i].final_score >= results[i + 1].final_score, \
                f"Not sorted: {results[i].final_score} < {results[i+1].final_score}"

    def test_mock_field_types_correct(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        results = retrieve('KYC requirements', junior_analyst_ctx, mock_mode=True)
        for r in results:
            d = r.document
            assert isinstance(d.doc_id, str) and d.doc_id
            assert isinstance(d.content, str) and d.content
            assert isinstance(d.jurisdiction, str)
            assert isinstance(d.valid_roles, list)
            assert all(isinstance(role, str) for role in d.valid_roles)
            assert isinstance(d.effective_date, date)
            assert d.superseded_date is None or isinstance(d.superseded_date, date)
            assert isinstance(d.risk_score, float)
            assert isinstance(d.risk_level, str)
            assert isinstance(r.semantic_score, float)
            assert isinstance(r.final_score, float)
            assert isinstance(r.risk_score, float)

    def test_mock_scores_are_positive(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        results = retrieve('KYC requirements', junior_analyst_ctx, mock_mode=True)
        for r in results:
            assert r.final_score > 0, f"final_score should be > 0, got {r.final_score}"
            assert r.semantic_score > 0


# ============================================================================
# TEST GROUP 2: M5–M6 — Generation Interface (generate)
# ============================================================================

class TestGenerationInterface:
    """Verify generate() mock_mode contract (Member 2 — Amala, M5+M6)."""

    def test_mock_returns_compliance_response(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate
        docs = retrieve('SEBI disclosure', junior_analyst_ctx, mock_mode=True)
        resp = generate('SEBI disclosure requirements?', docs, junior_analyst_ctx, mock_mode=True)
        assert isinstance(resp, ComplianceResponse)

    def test_mock_answer_is_non_empty_string(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate
        docs = retrieve('SEBI disclosure', junior_analyst_ctx, mock_mode=True)
        resp = generate('SEBI disclosure requirements?', docs, junior_analyst_ctx, mock_mode=True)
        assert isinstance(resp.answer, str) and len(resp.answer) > 0

    def test_mock_compliance_status_is_valid(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate
        docs = retrieve('SEBI disclosure', junior_analyst_ctx, mock_mode=True)
        resp = generate('SEBI disclosure requirements?', docs, junior_analyst_ctx, mock_mode=True)
        assert resp.compliance_status in ('PASS', 'WARNING', 'FAIL')

    def test_mock_violations_is_list(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate
        docs = retrieve('test', junior_analyst_ctx, mock_mode=True)
        resp = generate('test', docs, junior_analyst_ctx, mock_mode=True)
        assert isinstance(resp.violations, list)

    def test_mock_leakage_risk_is_valid(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate
        docs = retrieve('test', junior_analyst_ctx, mock_mode=True)
        resp = generate('test', docs, junior_analyst_ctx, mock_mode=True)
        assert resp.leakage_risk in ('NONE', 'LOW', 'HIGH')

    def test_mock_confidence_score_in_range(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate
        docs = retrieve('test', junior_analyst_ctx, mock_mode=True)
        resp = generate('test', docs, junior_analyst_ctx, mock_mode=True)
        assert 0.0 <= resp.confidence_score <= 1.0

    def test_mock_sources_are_financial_documents(self, junior_analyst_ctx):
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate
        docs = retrieve('test', junior_analyst_ctx, mock_mode=True)
        resp = generate('test', docs, junior_analyst_ctx, mock_mode=True)
        for s in resp.sources:
            assert isinstance(s, FinancialDocument)


# ============================================================================
# TEST GROUP 3: M7 — Agent Interface (agent_run)
# ============================================================================

class TestAgentInterface:
    """Verify agent_run() mock_mode contract (Member 2 — Amala, M7)."""

    def test_mock_returns_agent_response(self, compliance_officer_ctx):
        from Finguard_rag.agent.interface import agent_run
        resp = agent_run(
            'What insider trading rules apply under SEBI vs Companies Act?',
            compliance_officer_ctx,
            mock_mode=True,
        )
        assert isinstance(resp, AgentResponse)

    def test_mock_final_response_is_compliance_response(self, compliance_officer_ctx):
        from Finguard_rag.agent.interface import agent_run
        resp = agent_run('test', compliance_officer_ctx, mock_mode=True)
        assert isinstance(resp.final_response, ComplianceResponse)

    def test_mock_agent_trace_is_list_of_dicts(self, compliance_officer_ctx):
        from Finguard_rag.agent.interface import agent_run
        resp = agent_run('test', compliance_officer_ctx, mock_mode=True)
        assert isinstance(resp.agent_trace, list)
        assert len(resp.agent_trace) > 0
        for step in resp.agent_trace:
            assert isinstance(step, dict)
            assert 'type' in step, "Each trace step must have 'type'"
            assert 'content' in step, "Each trace step must have 'content'"

    def test_mock_trace_types_are_valid(self, compliance_officer_ctx):
        from Finguard_rag.agent.interface import agent_run
        resp = agent_run('test', compliance_officer_ctx, mock_mode=True)
        valid_types = {'THINK', 'ACT', 'OBS'}
        for step in resp.agent_trace:
            assert step['type'] in valid_types, \
                f"Invalid trace type: {step['type']}"

    def test_mock_total_iterations_positive(self, compliance_officer_ctx):
        from Finguard_rag.agent.interface import agent_run
        resp = agent_run('test', compliance_officer_ctx, mock_mode=True)
        assert isinstance(resp.total_iterations, int)
        assert resp.total_iterations > 0

    def test_mock_final_response_has_valid_status(self, compliance_officer_ctx):
        from Finguard_rag.agent.interface import agent_run
        resp = agent_run('test', compliance_officer_ctx, mock_mode=True)
        assert resp.final_response.compliance_status in ('PASS', 'WARNING', 'FAIL')

    def test_mock_final_response_answer_is_non_empty(self, compliance_officer_ctx):
        from Finguard_rag.agent.interface import agent_run
        resp = agent_run('test', compliance_officer_ctx, mock_mode=True)
        assert isinstance(resp.final_response.answer, str)
        assert len(resp.final_response.answer) > 0


# ============================================================================
# TEST GROUP 4: M8–M9 — Defense Interface (defend)
# ============================================================================

class TestDefenseInterface:
    """Verify defend() mock_mode contract (Member 3 — Ardra, M8+M9)."""

    def test_mock_returns_dict_with_defense_fields(self, junior_analyst_ctx):
        from Finguard_rag.defense.interface import defend
        from Finguard_rag.retrieval.interface import retrieve
        docs = retrieve('KYC requirements', junior_analyst_ctx, mock_mode=True)
        result = defend(
            session_id=junior_analyst_ctx.session_id,
            user_id=junior_analyst_ctx.user_id,
            role=junior_analyst_ctx.role,
            query='KYC requirements',
            response='Sample response about KYC...',
            source_docs=docs,
            user_context=junior_analyst_ctx,
            mock_mode=True,
        )
        assert isinstance(result, dict)
        required_keys = {
            'leakage_risk', 'leakage_details',
            'conflict_detected', 'conflicting_rules',
            'conservative_recommendation',
        }
        assert required_keys.issubset(result.keys()), \
            f"Missing keys: {required_keys - set(result.keys())}"

    def test_mock_leakage_risk_valid(self, junior_analyst_ctx):
        from Finguard_rag.defense.interface import defend
        from Finguard_rag.retrieval.interface import retrieve
        docs = retrieve('test', junior_analyst_ctx, mock_mode=True)
        result = defend(
            session_id='sess-test', user_id='test@test.com',
            role='junior_analyst', query='test',
            response='test response', source_docs=docs,
            mock_mode=True,
        )
        assert result['leakage_risk'] in ('NONE', 'LOW', 'HIGH')

    def test_mock_conflict_detected_is_bool(self, junior_analyst_ctx):
        from Finguard_rag.defense.interface import defend
        from Finguard_rag.retrieval.interface import retrieve
        docs = retrieve('test', junior_analyst_ctx, mock_mode=True)
        result = defend(
            session_id='sess-test', user_id='test@test.com',
            role='junior_analyst', query='test',
            response='test response', source_docs=docs,
            mock_mode=True,
        )
        assert isinstance(result['conflict_detected'], bool)


# ============================================================================
# TEST GROUP 5: Cross-Module Integration (retrieve → generate → agent)
# ============================================================================

class TestCrossModuleIntegration:
    """Verify end-to-end data flow between modules in mock_mode."""

    def test_retrieve_output_feeds_into_generate(self, junior_analyst_ctx):
        """Section 9 contract: retrieve() output is accepted by generate()."""
        from Finguard_rag.retrieval.interface import retrieve
        from Finguard_rag.generation.interface import generate
        docs = retrieve('SEBI LODR', junior_analyst_ctx, mock_mode=True)
        resp = generate('What are SEBI LODR rules?', docs, junior_analyst_ctx, mock_mode=True)
        assert isinstance(resp, ComplianceResponse)
        assert resp.compliance_status == 'PASS'

    def test_agent_orchestrates_full_pipeline(self, compliance_officer_ctx):
        """Agent mock should return a complete response with trace."""
        from Finguard_rag.agent.interface import agent_run
        resp = agent_run(
            'Compare SEBI and Companies Act insider trading rules',
            compliance_officer_ctx,
            mock_mode=True,
        )
        assert isinstance(resp, AgentResponse)
        assert isinstance(resp.final_response, ComplianceResponse)
        assert len(resp.agent_trace) > 0
        assert resp.total_iterations > 0

    def test_schema_imports_from_response_schema(self):
        """response_schema.py re-exports work correctly."""
        from Finguard_rag.schemas.response_schema import (
            ComplianceResponse as CR,
            DefenseResult as DR,
            AgentResponse as AR,
            RankedDocument as RD,
        )
        assert CR is ComplianceResponse
        assert AR is AgentResponse
        assert RD is RankedDocument
