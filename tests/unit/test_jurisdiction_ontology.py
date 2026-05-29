"""PART 1 — Unit Tests: test_jurisdiction_ontology.py"""
import pytest
from Finguard_rag.defense.jurisdiction_ontology import get_all_patterns, CONFLICT_PATTERNS


class TestJurisdictionOntology:
    def test_patterns_not_empty(self):
        patterns = get_all_patterns()
        assert len(patterns) > 0

    def test_in_global_lease_conflict_exists(self):
        found = any(
            p.jurisdiction_a == "IN" and p.jurisdiction_b == "GLOBAL" and p.topic == "lease_accounting"
            for p in CONFLICT_PATTERNS
        )
        assert found

    def test_in_eu_data_privacy_conflict_exists(self):
        found = any(
            p.jurisdiction_a == "IN" and p.jurisdiction_b == "EU" and p.topic == "data_privacy"
            for p in CONFLICT_PATTERNS
        )
        assert found

    def test_in_sg_aml_conflict_exists(self):
        found = any(
            p.jurisdiction_a == "IN" and p.jurisdiction_b == "SG" and p.topic == "aml_cft"
            for p in CONFLICT_PATTERNS
        )
        assert found

    def test_in_in_insider_trading_exists(self):
        found = any(
            p.jurisdiction_a == "IN" and p.jurisdiction_b == "IN" and p.topic == "insider_trading_disclosure"
            for p in CONFLICT_PATTERNS
        )
        assert found

    def test_pattern_has_required_fields(self):
        for p in CONFLICT_PATTERNS:
            assert p.jurisdiction_a
            assert p.jurisdiction_b
            assert p.topic
            assert p.description
            assert p.conservative_recommendation
            assert len(p.trigger_keywords) > 0
