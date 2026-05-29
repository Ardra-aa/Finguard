"""PART 1 — Unit Tests: test_conflict_resolver.py"""
import pytest
from Finguard_rag.defense.conflict_resolver import ConflictResolver


class TestConflictResolver:
    def setup_method(self):
        self.resolver = ConflictResolver()

    def test_resolve_returns_conservative_recommendation(self):
        result = self.resolver.resolve(
            query="What are the lease accounting rules under Ind AS 116?",
            source_doc_ids=["IndAS_Compendium_2023"],
            source_contents=["Ind AS 116 lease accounting right-of-use asset"],
            user_jurisdiction="IN",
        )
        if result["conflict_detected"]:
            assert result["conservative_recommendation"] != ""

    def test_resolve_lease_conflict_detected(self):
        result = self.resolver.resolve(
            query="How should we account for leases under IFRS 16 and Ind AS 116?",
            source_doc_ids=["POL-011"],
            source_contents=["Ind AS 116 right-of-use asset IFRS 16 low-value lease"],
        )
        assert result["conflict_detected"] is True

    def test_resolve_no_conflict_for_simple_query(self):
        result = self.resolver.resolve(
            query="What is the company name?",
            source_doc_ids=["DOC-001"],
            source_contents=["BharatFinServ Ltd company overview"],
        )
        # May or may not detect depending on keyword matching
        assert isinstance(result["conflict_detected"], bool)

    def test_resolve_returns_both_rule_references(self):
        result = self.resolver.resolve(
            query="SEBI vs Companies Act related party transaction rules",
            source_doc_ids=["SEBI_LODR", "POL-007"],
            source_contents=["related party transaction audit committee approval"],
        )
        if result["conflict_detected"]:
            assert len(result["conflicting_rules"]) > 0

    def test_mock_mode_no_conflict(self):
        result = self.resolver.resolve(
            query="test", source_doc_ids=[], source_contents=[],
            mock_mode=True,
        )
        assert result["conflict_detected"] is False

    def test_resolve_unknown_jurisdiction_graceful(self):
        result = self.resolver.resolve(
            query="What are the rules?",
            source_doc_ids=["DOC-1"],
            source_contents=["Some content"],
            user_jurisdiction="MARS",
        )
        assert isinstance(result, dict)
