"""PART 1 — Unit Tests: test_session_tracker.py"""
import pytest
from Finguard_rag.defense.session_tracker import SessionTracker


class TestSessionTracker:
    def setup_method(self):
        # Reset singleton for test isolation
        SessionTracker._instance = None
        self.tracker = SessionTracker()

    def test_new_session_starts_with_zero_queries(self):
        session = self.tracker.get_or_create("s1", "u1", "ceo")
        assert len(session.queries) == 0

    def test_add_query_increments_count(self):
        self.tracker.add_query("s1", "u1", "ceo", "q1", [0.1]*384, "LOW", ["D1"])
        queries = self.tracker.get_queries("s1")
        assert len(queries) == 1

    def test_multiple_queries_tracked(self):
        self.tracker.add_query("s1", "u1", "ceo", "q1", [0.1]*384, "LOW", ["D1"])
        self.tracker.add_query("s1", "u1", "ceo", "q2", [0.2]*384, "HIGH", ["D2"])
        queries = self.tracker.get_queries("s1")
        assert len(queries) == 2

    def test_different_sessions_independent(self):
        self.tracker.add_query("s1", "u1", "ceo", "q1", [0.1]*384, "LOW", ["D1"])
        self.tracker.add_query("s2", "u2", "cfo", "q2", [0.2]*384, "LOW", ["D2"])
        assert len(self.tracker.get_queries("s1")) == 1
        assert len(self.tracker.get_queries("s2")) == 1

    def test_clear_session_removes_data(self):
        self.tracker.add_query("s1", "u1", "ceo", "q1", [0.1]*384, "LOW", ["D1"])
        self.tracker.clear_session("s1")
        assert self.tracker.get_session("s1") is None

    def test_get_report_for_valid_session(self):
        self.tracker.add_query("s1", "u1", "ceo", "q1", [0.1]*384, "LOW", ["D1"])
        report = self.tracker.get_report("s1")
        assert report["query_count"] == 1
        assert report["user_id"] == "u1"

    def test_get_report_for_missing_session(self):
        report = self.tracker.get_report("nonexistent")
        assert "error" in report

    def test_set_leakage_risk(self):
        self.tracker.get_or_create("s1", "u1", "ceo")
        self.tracker.set_leakage_risk("s1", "HIGH", "Test alert")
        session = self.tracker.get_session("s1")
        assert session.leakage_risk == "HIGH"
        assert "Test alert" in session.alerts

    def test_get_all_sessions(self):
        self.tracker.get_or_create("s1", "u1", "ceo")
        self.tracker.get_or_create("s2", "u2", "cfo")
        sessions = self.tracker.get_all_sessions()
        assert len(sessions) == 2
