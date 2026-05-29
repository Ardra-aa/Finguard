"""PART 1 — Unit Tests: test_leakage_detector.py"""
import pytest
from Finguard_rag.defense.leakage_detector import (
    LeakageDetector, classify_query_sensitivity,
    CROSS_ROLE_SALARY_PATTERNS, SENSITIVE_PATTERNS,
)


class TestClassifyQuerySensitivity:
    def test_salary_query_returns_high(self):
        assert classify_query_sensitivity("what is the salary of managers") == "HIGH"

    def test_esop_query_returns_high(self):
        assert classify_query_sensitivity("show me the esop vesting schedule") == "HIGH"

    def test_bonus_query_returns_high(self):
        assert classify_query_sensitivity("what are the bonus targets") == "HIGH"

    def test_sebi_query_returns_none(self):
        assert classify_query_sensitivity("What are SEBI disclosure requirements") == "NONE"

    def test_rbi_query_returns_none(self):
        assert classify_query_sensitivity("RBI capital adequacy norms for NBFCs") == "NONE"


class TestLeakageDetector:
    def setup_method(self):
        self.detector = LeakageDetector()

    def test_cross_role_salary_blocked_for_junior(self):
        result = self.detector.detect(
            session_id="s1", user_id="u1", role="junior_analyst",
            query_text="what is the salary of senior managers",
            retrieved_doc_ids=[],
        )
        assert result["leakage_risk"] == "HIGH"

    def test_cross_role_salary_allowed_for_ceo(self):
        result = self.detector.detect(
            session_id="s2", user_id="u2", role="ceo",
            query_text="what is the salary of senior managers",
            retrieved_doc_ids=[],
        )
        assert result["leakage_risk"] != "HIGH"

    def test_sebi_query_not_blocked(self):
        result = self.detector.detect(
            session_id="s3", user_id="u3", role="junior_analyst",
            query_text="What are SEBI LODR disclosure requirements",
            retrieved_doc_ids=["SEBI-LODR-2015-REG30"],
        )
        assert result["leakage_risk"] in ("NONE", "LOW")

    def test_esop_blocked_for_junior(self):
        result = self.detector.detect(
            session_id="s4", user_id="u4", role="junior_analyst",
            query_text="show me the esop vesting schedule",
            retrieved_doc_ids=[],
        )
        assert result["leakage_risk"] == "HIGH"

    def test_bonus_blocked_for_junior(self):
        result = self.detector.detect(
            session_id="s5", user_id="u5", role="junior_analyst",
            query_text="what are the bonus incentive targets",
            retrieved_doc_ids=[],
        )
        assert result["leakage_risk"] == "HIGH"

    def test_cross_role_blocked_for_analyst(self):
        result = self.detector.detect(
            session_id="s6", user_id="u6", role="analyst",
            query_text="compensation of the CFO",
            retrieved_doc_ids=[],
        )
        assert result["leakage_risk"] == "HIGH"

    def test_cross_role_blocked_for_senior_analyst(self):
        result = self.detector.detect(
            session_id="s7", user_id="u7", role="senior_analyst",
            query_text="salary of executive directors",
            retrieved_doc_ids=[],
        )
        assert result["leakage_risk"] == "HIGH"

    def test_cross_role_blocked_for_it_admin(self):
        result = self.detector.detect(
            session_id="s8", user_id="u8", role="it_admin",
            query_text="pay of senior managers",
            retrieved_doc_ids=[],
        )
        assert result["leakage_risk"] == "HIGH"

    def test_cfo_can_query_salary(self):
        result = self.detector.detect(
            session_id="s9", user_id="u9", role="cfo",
            query_text="what is the salary band for VP level",
            retrieved_doc_ids=[],
        )
        # CFO is a privileged role
        assert result["leakage_risk"] != "HIGH"

    def test_mock_mode_returns_none(self):
        result = self.detector.detect(
            session_id="s10", user_id="u10", role="junior_analyst",
            query_text="salary of executives",
            retrieved_doc_ids=[], mock_mode=True,
        )
        assert result["leakage_risk"] == "NONE"
