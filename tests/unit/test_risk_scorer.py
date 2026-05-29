"""PART 1 — Unit Tests: test_risk_scorer.py"""
import pytest
from datetime import date
from Finguard_rag.retrieval.risk_scorer import score_and_rank, MIN_FINAL_SCORE, ALPHA, BETA


def _meta(doc_id="D1", risk_score=0.2, chunk_text="content"):
    return {
        "doc_id": doc_id, "_chunk_text": chunk_text,
        "jurisdiction": "IN", "regulatory_scope": "securities",
        "valid_roles": "ceo,junior_analyst", "effective_date": "2020-01-01",
        "superseded_date": "", "version": "1.0", "risk_level": "LOW",
        "risk_score": str(risk_score), "source_file": "test.pdf",
    }


class TestRiskScorer:
    def test_high_relevance_low_risk_gets_high_score(self):
        candidates = [(_meta(risk_score=0.1), 0.1)]  # distance=0.1 -> sim=0.9
        ranked = score_and_rank(candidates)
        assert len(ranked) == 1
        assert ranked[0].final_score > 0.5

    def test_high_risk_gets_penalized(self):
        low_risk = [(_meta(doc_id="LR", risk_score=0.1), 0.2)]
        high_risk = [(_meta(doc_id="HR", risk_score=0.9), 0.2)]
        lr = score_and_rank(low_risk)
        hr = score_and_rank(high_risk)
        assert lr[0].final_score > hr[0].final_score if hr else True

    def test_below_min_score_filtered(self):
        candidates = [(_meta(risk_score=0.9), 0.9)]  # sim=0.1, high risk
        ranked = score_and_rank(candidates)
        # 0.7*0.1 - 0.3*0.9 = 0.07 - 0.27 = -0.2 < MIN_FINAL_SCORE
        assert len(ranked) == 0

    def test_sorted_descending(self):
        candidates = [
            (_meta(doc_id="A", risk_score=0.3), 0.3),
            (_meta(doc_id="B", risk_score=0.1), 0.1),
        ]
        ranked = score_and_rank(candidates)
        if len(ranked) >= 2:
            assert ranked[0].final_score >= ranked[1].final_score

    def test_empty_input(self):
        assert score_and_rank([]) == []

    def test_zero_risk_no_penalty(self):
        candidates = [(_meta(risk_score=0.0), 0.2)]
        ranked = score_and_rank(candidates)
        assert len(ranked) == 1
        expected = ALPHA * 0.8 - BETA * 0.0  # 0.56
        assert abs(ranked[0].final_score - expected) < 0.01
