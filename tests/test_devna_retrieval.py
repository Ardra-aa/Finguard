"""
tests/test_devna_retrieval.py
Devna Thunnan — Retrieval pipeline integration tests

Tests mock_mode, real retrieval with RBAC filtering, and role-based access.
"""

import sys
from pathlib import Path

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import date
from Finguard_rag.retrieval.interface import retrieve
from Finguard_rag.schemas.document_schema import UserContext, RankedDocument

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"
results_log = []


def check(label, fn):
    try:
        fn()
        print(f"[{PASS}] {label}")
        results_log.append(True)
    except Exception as e:
        print(f"[{FAIL}] {label}")
        print(f"         {type(e).__name__}: {e}")
        results_log.append(False)


# ============================================================================
# TEST 1: Mock Mode
# ============================================================================
def test_mock_mode():
    print("\n" + "=" * 60)
    print("  TEST 1: Mock Mode")
    print("=" * 60)

    ctx = UserContext(
        user_id='arjun.kumar@bharatfinserv.in',
        role='junior_analyst',
        jurisdiction='IN',
        reference_date=date.today(),
        session_id='test-session-001',
    )
    results = retrieve('KYC requirements', ctx, mock_mode=True)
    print(f"  Mock mode results: {len(results)}")

    assert len(results) == 3, f"Expected 3 mock results, got {len(results)}"
    assert all(isinstance(r, RankedDocument) for r in results)
    assert all(r.final_score > 0 for r in results)
    # Check descending order
    for i in range(len(results) - 1):
        assert results[i].final_score >= results[i + 1].final_score, \
            f"Results not sorted descending: {results[i].final_score} < {results[i+1].final_score}"

    for r in results:
        print(f"    doc_id={r.document.doc_id}, score={r.final_score:.3f}")


check("Mock mode returns 3 sorted RankedDocuments", test_mock_mode)


# ============================================================================
# TEST 2: Real Retrieval — junior_analyst, IN jurisdiction
# ============================================================================
def test_real_junior_analyst():
    print("\n" + "=" * 60)
    print("  TEST 2: Real Retrieval — junior_analyst / IN")
    print("=" * 60)

    ctx = UserContext(
        user_id='arjun.kumar@bharatfinserv.in',
        role='junior_analyst',
        jurisdiction='IN',
        reference_date=date.today(),
        session_id='test-session-001',
    )
    results = retrieve('KYC requirements for customers', ctx, top_k=5)
    print(f"  Results count: {len(results)}")

    assert len(results) > 0, "Expected at least 1 result for KYC query"

    for r in results:
        print(f"    doc_id={r.document.doc_id}, "
              f"roles={r.document.valid_roles}, "
              f"jur={r.document.jurisdiction}, "
              f"final_score={r.final_score:.3f}")

        # RBAC check: junior_analyst must be in valid_roles
        assert 'junior_analyst' in r.document.valid_roles, \
            f"RBAC violation: junior_analyst not in {r.document.valid_roles} for {r.document.doc_id}"

        # Jurisdiction check: must include IN
        jur = r.document.jurisdiction
        # jurisdiction is stored as a string like "IN" or "IN,SG"
        assert 'IN' in jur, \
            f"Jurisdiction violation: 'IN' not in '{jur}' for {r.document.doc_id}"

        # Score threshold check
        assert r.final_score >= 0.3, \
            f"Score below threshold: {r.final_score} for {r.document.doc_id}"


check("Real retrieval: junior_analyst gets only IN-jurisdiction, role-accessible docs", test_real_junior_analyst)


# ============================================================================
# TEST 3: CEO gets more documents (salary/compensation query)
# ============================================================================
def test_ceo_broader_access():
    print("\n" + "=" * 60)
    print("  TEST 3: CEO vs junior_analyst access breadth")
    print("=" * 60)

    # CEO context
    ceo_ctx = UserContext(
        user_id='rahul.sharma@bharatfinserv.in',
        role='ceo',
        jurisdiction='IN',
        reference_date=date.today(),
        session_id='test-session-002',
    )
    ceo_results = retrieve('salary compensation policy', ceo_ctx, top_k=5)
    print(f"  CEO results count: {len(ceo_results)}")

    for r in ceo_results:
        print(f"    doc_id={r.document.doc_id}, "
              f"roles={r.document.valid_roles}, "
              f"final_score={r.final_score:.3f}")

    # Junior analyst with same query
    jr_ctx = UserContext(
        user_id='arjun.kumar@bharatfinserv.in',
        role='junior_analyst',
        jurisdiction='IN',
        reference_date=date.today(),
        session_id='test-session-003',
    )
    jr_results = retrieve('salary compensation policy', jr_ctx, top_k=5)
    print(f"  Junior analyst results count: {len(jr_results)}")

    for r in jr_results:
        print(f"    doc_id={r.document.doc_id}, "
              f"roles={r.document.valid_roles}, "
              f"final_score={r.final_score:.3f}")

    # CEO should get >= junior_analyst results (broader RBAC access)
    assert len(ceo_results) >= len(jr_results), \
        f"CEO ({len(ceo_results)}) should get >= junior_analyst ({len(jr_results)}) results"

    # Verify CEO role appears in all CEO results
    for r in ceo_results:
        assert 'ceo' in r.document.valid_roles, \
            f"RBAC violation: 'ceo' not in {r.document.valid_roles}"


check("CEO gets >= junior_analyst results for same query", test_ceo_broader_access)


# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 60)
passed = sum(results_log)
total = len(results_log)
status = "ALL PASSED" if passed == total else f"{total - passed} FAILED"
print(f"  Results: {passed}/{total} passed  [{status}]")
print("=" * 60)
sys.exit(0 if passed == total else 1)
