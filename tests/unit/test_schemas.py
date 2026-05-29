"""PART 1 — Unit Tests: test_schemas.py"""
import pytest
from datetime import date
from Finguard_rag.schemas.document_schema import (
    FinancialDocument, UserContext, RankedDocument,
    ComplianceResponse, DefenseResult, AgentResponse,
)


# ── FinancialDocument ──────────────────────────────────────────────────────
class TestFinancialDocument:
    def test_create_with_required_fields(self):
        doc = FinancialDocument(
            doc_id="SEBI-001", content="test content", jurisdiction="IN",
            regulatory_scope="securities",
            valid_roles=["ceo"], effective_date=date(2023, 1, 1),
            superseded_date=None,
        )
        assert doc.doc_id == "SEBI-001"
        assert doc.content == "test content"
        assert doc.jurisdiction == "IN"

    def test_default_values(self):
        doc = FinancialDocument(
            doc_id="X", content="c", jurisdiction="IN",
            regulatory_scope="banking", valid_roles=[],
            effective_date=date(2020, 1, 1), superseded_date=None,
        )
        assert doc.version == "1.0"
        assert doc.risk_level == "MEDIUM"
        assert doc.risk_score == 0.5
        assert doc.source_file == ""
        assert doc.source_url is None
        assert doc.embedding is None

    def test_superseded_date_can_be_none(self):
        doc = FinancialDocument(
            doc_id="X", content="c", jurisdiction="IN",
            regulatory_scope="corporate", valid_roles=[],
            effective_date=date(2020, 1, 1), superseded_date=None,
        )
        assert doc.superseded_date is None

    def test_superseded_date_can_be_date(self):
        doc = FinancialDocument(
            doc_id="X", content="c", jurisdiction="IN",
            regulatory_scope="corporate", valid_roles=[],
            effective_date=date(2020, 1, 1), superseded_date=date(2023, 6, 1),
        )
        assert doc.superseded_date == date(2023, 6, 1)


# ── UserContext ────────────────────────────────────────────────────────────
class TestUserContext:
    def test_create_user_context(self):
        ctx = UserContext(
            user_id="test@test.com", role="junior_analyst",
            jurisdiction="IN", reference_date=date.today(),
            session_id="s1",
        )
        assert ctx.role == "junior_analyst"
        assert ctx.jurisdiction == "IN"

    def test_user_context_stores_session_id(self):
        ctx = UserContext(
            user_id="u1", role="ceo", jurisdiction="IN",
            reference_date=date.today(), session_id="sess-xyz",
        )
        assert ctx.session_id == "sess-xyz"


# ── RankedDocument ─────────────────────────────────────────────────────────
class TestRankedDocument:
    def _make_doc(self):
        return FinancialDocument(
            doc_id="D1", content="c", jurisdiction="IN",
            regulatory_scope="securities", valid_roles=["ceo"],
            effective_date=date(2023, 1, 1), superseded_date=None,
        )

    def test_ranked_document_creation(self):
        rd = RankedDocument(
            document=self._make_doc(),
            semantic_score=0.9, risk_score=0.2, final_score=0.55,
        )
        assert rd.semantic_score == 0.9
        assert rd.final_score == 0.55

    def test_score_between_0_and_1(self):
        rd = RankedDocument(
            document=self._make_doc(),
            semantic_score=0.5, risk_score=0.3, final_score=0.26,
        )
        assert 0.0 <= rd.semantic_score <= 1.0
        assert 0.0 <= rd.risk_score <= 1.0


# ── ComplianceResponse ────────────────────────────────────────────────────
class TestComplianceResponse:
    def test_compliance_response_pass(self):
        cr = ComplianceResponse(
            answer="test", sources=[], compliance_status="PASS",
            violations=[], conflicts=[], leakage_risk="NONE",
            confidence_score=0.9,
        )
        assert cr.compliance_status == "PASS"

    def test_compliance_response_fail(self):
        cr = ComplianceResponse(
            answer="blocked", sources=[], compliance_status="FAIL",
            violations=["SEBI_001"], conflicts=[], leakage_risk="NONE",
            confidence_score=0.0,
        )
        assert cr.compliance_status == "FAIL"
        assert len(cr.violations) == 1

    def test_agent_trace_default_none(self):
        cr = ComplianceResponse(
            answer="a", sources=[], compliance_status="PASS",
            violations=[], conflicts=[], leakage_risk="NONE",
            confidence_score=0.9,
        )
        assert cr.agent_trace is None


# ── DefenseResult ──────────────────────────────────────────────────────────
class TestDefenseResult:
    def test_defense_result_none(self):
        dr = DefenseResult(
            leakage_risk="NONE", leakage_details=[],
            conflict_detected=False, conflicting_rules=[],
            conservative_recommendation="",
        )
        assert dr.leakage_risk == "NONE"

    def test_defense_result_high(self):
        dr = DefenseResult(
            leakage_risk="HIGH", leakage_details=["Cross-role detected"],
            conflict_detected=False, conflicting_rules=[],
            conservative_recommendation="",
        )
        assert dr.leakage_risk == "HIGH"


# ── AgentResponse ──────────────────────────────────────────────────────────
class TestAgentResponse:
    def test_agent_response_creation(self):
        cr = ComplianceResponse(
            answer="a", sources=[], compliance_status="PASS",
            violations=[], conflicts=[], leakage_risk="NONE",
            confidence_score=0.9,
        )
        ar = AgentResponse(
            final_response=cr, agent_trace=[{"type": "THINK", "content": "t"}],
            total_iterations=1,
        )
        assert isinstance(ar.agent_trace, list)
        assert ar.total_iterations == 1
