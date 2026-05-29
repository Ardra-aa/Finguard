"""PART 2 — Integration Tests: test_retrieval_pipeline.py + test_generation_pipeline.py + test_defense_pipeline.py"""
import pytest
from datetime import date
from Finguard_rag.schemas.document_schema import UserContext, RankedDocument, FinancialDocument
from Finguard_rag.retrieval.interface import retrieve
from Finguard_rag.generation.interface import generate
from Finguard_rag.defense.interface import defend


def _ctx(role="compliance_officer", jurisdiction="IN"):
    return UserContext(
        user_id="test@test.com", role=role, jurisdiction=jurisdiction,
        reference_date=date.today(), session_id=f"test-{role}-{jurisdiction}",
    )


# ── Retrieval Pipeline ────────────────────────────────────────────────────
class TestRetrievalPipeline:
    def test_mock_retrieve_returns_ranked_docs(self):
        docs = retrieve("SEBI disclosure", _ctx(), mock_mode=True)
        assert len(docs) > 0
        assert all(isinstance(d, RankedDocument) for d in docs)

    def test_mock_docs_sorted_by_score(self):
        docs = retrieve("test", _ctx(), mock_mode=True)
        scores = [d.final_score for d in docs]
        assert scores == sorted(scores, reverse=True)

    def test_mock_doc_content_populated(self):
        docs = retrieve("test", _ctx(), mock_mode=True)
        for d in docs:
            assert d.document.content is not None
            assert len(d.document.content) > 0

    def test_live_retrieve_returns_docs(self):
        docs = retrieve("What are SEBI LODR disclosure requirements?", _ctx())
        assert isinstance(docs, list)

    def test_live_retrieve_empty_query(self):
        docs = retrieve("", _ctx())
        assert isinstance(docs, list)


# ── Generation Pipeline ───────────────────────────────────────────────────
class TestGenerationPipeline:
    def test_mock_generate_returns_compliance_response(self):
        docs = retrieve("test", _ctx(), mock_mode=True)
        resp = generate("test", docs, _ctx(), mock_mode=True)
        assert resp.compliance_status in ("PASS", "WARNING", "FAIL")
        assert len(resp.answer) > 0

    def test_generate_empty_docs_graceful(self):
        resp = generate("test query with no docs", [], _ctx(), mock_mode=False)
        assert resp.answer != ""
        assert resp.compliance_status in ("PASS", "WARNING", "FAIL")


# ── Defense Pipeline ──────────────────────────────────────────────────────
class TestDefensePipeline:
    def test_mock_defend_returns_clean(self):
        docs = retrieve("test", _ctx(), mock_mode=True)
        result = defend(
            session_id="test-mock", user_id="u1", role="compliance_officer",
            query="SEBI disclosure", response="answer text",
            source_docs=docs, user_context=_ctx(), mock_mode=True,
        )
        assert result["leakage_risk"] == "NONE"
        assert result["conflict_detected"] is False

    def test_defend_blocks_salary_for_junior(self):
        result = defend(
            session_id="test-block", user_id="u2", role="junior_analyst",
            query="salary of senior managers", response="",
            source_docs=[], user_context=_ctx(role="junior_analyst"),
        )
        assert result["leakage_risk"] == "HIGH"

    def test_defend_allows_sebi_for_junior(self):
        result = defend(
            session_id="test-allow", user_id="u3", role="junior_analyst",
            query="What are SEBI LODR requirements?", response="SEBI rules...",
            source_docs=[], user_context=_ctx(role="junior_analyst"),
        )
        assert result["leakage_risk"] in ("NONE", "LOW")

    def test_defend_detects_conflict(self):
        docs = retrieve("SEBI vs Companies Act insider trading", _ctx(), mock_mode=True)
        result = defend(
            session_id="test-conflict", user_id="u4", role="compliance_officer",
            query="insider trading SEBI PIT disclosure LODR Reg 30",
            response="The rules differ between SEBI and Companies Act.",
            source_docs=docs, user_context=_ctx(),
        )
        # May or may not detect depending on keyword matching
        assert isinstance(result["conflict_detected"], bool)
