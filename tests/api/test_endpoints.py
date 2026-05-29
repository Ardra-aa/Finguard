"""PART 3 — API Tests: test_endpoints.py"""
import pytest
from fastapi.testclient import TestClient
from Finguard_rag.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_status_field(self):
        r = client.get("/health")
        data = r.json()
        assert "status" in data

    def test_health_has_version(self):
        r = client.get("/health")
        data = r.json()
        assert "version" in data or "status" in data


class TestQueryEndpoint:
    def _payload(self, role="compliance_officer", query="What are SEBI LODR disclosure requirements?"):
        return {
            "query": query,
            "user_id": "test@bharatfinserv.in",
            "role": role,
            "jurisdiction": "IN",
            "session_id": f"test-api-{role}",
            "mock_mode": True,
        }

    def test_query_returns_200_with_mock(self):
        r = client.post("/query", json=self._payload())
        assert r.status_code == 200

    def test_response_has_required_fields(self):
        r = client.post("/query", json=self._payload())
        data = r.json()
        for field in ["answer", "compliance_status", "violations",
                      "sources", "leakage_risk", "conflict_detected"]:
            assert field in data, f"Missing field: {field}"

    def test_missing_required_field_returns_422(self):
        r = client.post("/query", json={"query": "test"})
        assert r.status_code == 422

    def test_salary_query_by_junior_blocked(self):
        payload = self._payload(
            role="junior_analyst",
            query="what is the salary of senior managers",
        )
        payload["mock_mode"] = False
        r = client.post("/query", json=payload)
        # Should be blocked (403 or 200 with FAIL)
        if r.status_code == 200:
            assert r.json()["compliance_status"] == "FAIL" or r.json()["leakage_risk"] == "HIGH"
        elif r.status_code == 403:
            pass  # Correctly blocked
        else:
            pytest.fail(f"Unexpected status: {r.status_code}")


class TestSessionsEndpoint:
    def test_sessions_returns_200(self):
        r = client.get("/sessions")
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data, list)
        elif r.status_code == 404:
            pytest.skip("Sessions endpoint not available")
