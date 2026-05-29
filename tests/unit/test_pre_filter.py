"""PART 1 — Unit Tests: test_pre_filter.py"""
import pytest
from datetime import date
from Finguard_rag.schemas.document_schema import UserContext
from Finguard_rag.retrieval.pre_filter import passes_pre_filter, post_filter


def _ctx(role="junior_analyst", jurisdiction="IN", ref_date=None):
    return UserContext(
        user_id="test@test.com", role=role, jurisdiction=jurisdiction,
        reference_date=ref_date or date.today(), session_id="s1",
    )


class TestPassesPreFilter:
    def test_matching_jurisdiction_passes(self):
        meta = {"valid_roles": "junior_analyst,ceo", "jurisdiction": "IN", "effective_date": "2020-01-01"}
        assert passes_pre_filter(meta, _ctx()) is True

    def test_non_matching_jurisdiction_blocked(self):
        meta = {"valid_roles": "junior_analyst", "jurisdiction": "EU", "effective_date": "2020-01-01"}
        assert passes_pre_filter(meta, _ctx(jurisdiction="IN")) is False

    def test_multi_jurisdiction_passes(self):
        meta = {"valid_roles": "junior_analyst", "jurisdiction": "IN,SG", "effective_date": "2020-01-01"}
        assert passes_pre_filter(meta, _ctx(jurisdiction="IN")) is True

    def test_global_jurisdiction_passes_any(self):
        meta = {"valid_roles": "junior_analyst", "jurisdiction": "GLOBAL", "effective_date": "2020-01-01"}
        assert passes_pre_filter(meta, _ctx(jurisdiction="SG")) is True

    def test_role_not_in_valid_roles_blocked(self):
        meta = {"valid_roles": "ceo", "jurisdiction": "IN", "effective_date": "2020-01-01"}
        assert passes_pre_filter(meta, _ctx(role="junior_analyst")) is False

    def test_role_in_valid_roles_passes(self):
        meta = {"valid_roles": "junior_analyst,ceo", "jurisdiction": "IN", "effective_date": "2020-01-01"}
        assert passes_pre_filter(meta, _ctx(role="junior_analyst")) is True

    def test_future_effective_date_blocked(self):
        meta = {"valid_roles": "ceo", "jurisdiction": "IN", "effective_date": "2099-01-01"}
        assert passes_pre_filter(meta, _ctx(role="ceo", ref_date=date(2024, 1, 1))) is False

    def test_past_effective_date_passes(self):
        meta = {"valid_roles": "ceo", "jurisdiction": "IN", "effective_date": "2020-01-01"}
        assert passes_pre_filter(meta, _ctx(role="ceo", ref_date=date(2024, 1, 1))) is True


class TestPostFilter:
    def test_empty_list_returns_empty(self):
        assert post_filter([], _ctx()) == []

    def test_filters_correctly(self):
        results = [
            ({"valid_roles": "ceo", "jurisdiction": "IN", "effective_date": "2020-01-01"}, 0.1),
            ({"valid_roles": "junior_analyst", "jurisdiction": "IN", "effective_date": "2020-01-01"}, 0.2),
        ]
        filtered = post_filter(results, _ctx(role="junior_analyst"))
        assert len(filtered) == 1
        assert filtered[0][1] == 0.2
