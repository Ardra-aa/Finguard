"""PART 1 — Unit Tests: test_prompt_builder.py"""
import pytest
from datetime import date
from Finguard_rag.schemas.document_schema import FinancialDocument, RankedDocument, UserContext
from Finguard_rag.generation.prompt_builder import build_prompt


def _ctx(role="compliance_officer"):
    return UserContext(
        user_id="test@test.com", role=role, jurisdiction="IN",
        reference_date=date.today(), session_id="s1",
    )

def _doc(doc_id="D1", content="This is regulatory content about SEBI."):
    return RankedDocument(
        document=FinancialDocument(
            doc_id=doc_id, content=content, jurisdiction="IN",
            regulatory_scope="securities", valid_roles=["compliance_officer"],
            effective_date=date(2023, 1, 1), superseded_date=None,
        ),
        semantic_score=0.9, risk_score=0.2, final_score=0.55,
    )


class TestPromptBuilder:
    def test_prompt_includes_query(self):
        prompt = build_prompt("What are SEBI rules?", [_doc()], _ctx())
        assert "What are SEBI rules?" in prompt

    def test_prompt_includes_role(self):
        prompt = build_prompt("test", [_doc()], _ctx(role="cfo"))
        assert "cfo" in prompt

    def test_prompt_includes_jurisdiction(self):
        prompt = build_prompt("test", [_doc()], _ctx())
        assert "IN" in prompt

    def test_prompt_includes_doc_content(self):
        prompt = build_prompt("test", [_doc(content="SEBI LODR Regulation 30 text")], _ctx())
        assert "SEBI LODR Regulation 30" in prompt

    def test_prompt_includes_doc_id_citation(self):
        prompt = build_prompt("test", [_doc(doc_id="SEBI-LODR-2015")], _ctx())
        assert "SEBI-LODR-2015" in prompt

    def test_empty_docs_graceful(self):
        prompt = build_prompt("test query", [], _ctx())
        assert "No relevant documents" in prompt

    def test_truncates_long_documents(self):
        long_content = "A" * 3000
        prompt = build_prompt("test", [_doc(content=long_content)], _ctx())
        # Content should be truncated to 1500
        assert len(prompt) < len(long_content) + 1000

    def test_max_5_docs(self):
        docs = [_doc(doc_id=f"D{i}", content=f"Content {i}") for i in range(10)]
        prompt = build_prompt("test", docs, _ctx())
        # Should include at most 5 sources
        source_count = prompt.count("[Source ")
        assert source_count <= 5
