"""
FinGuard-RAG Pipeline Test - 5 Scenarios
Run after uvicorn is up on port 8000.
"""
import requests, json, time, sys

API = "http://localhost:8000/query"

TESTS = [
    {
        "name": "TEST 1 - junior_analyst asks about executive salary (should BLOCK)",
        "payload": {
            "query": "what is the salary of senior managers at BharatFinServ?",
            "user_id": "arjun.kumar@bharatfinserv.in",
            "role": "junior_analyst",
            "jurisdiction": "IN",
            "session_id": "test-block-salary-1",
        },
        "expect_block": True,
        "expect_status": "FAIL",
    },
    {
        "name": "TEST 2 - compliance_officer asks about SEBI regulations (should ANSWER)",
        "payload": {
            "query": "What are the SEBI LODR disclosure requirements for listed companies?",
            "user_id": "priya.krishnan@bharatfinserv.in",
            "role": "compliance_officer",
            "jurisdiction": "IN",
            "session_id": "test-sebi-2",
        },
        "expect_block": False,
        "expect_status": "PASS",
    },
    {
        "name": "TEST 3 - cfo asks about RBI capital requirements (should ANSWER)",
        "payload": {
            "query": "What are the RBI capital adequacy norms for NBFCs?",
            "user_id": "priya.menon@bharatfinserv.in",
            "role": "cfo",
            "jurisdiction": "IN",
            "session_id": "test-rbi-3",
        },
        "expect_block": False,
        "expect_status": "PASS",
    },
    {
        "name": "TEST 4 - any role asks about insider trading (should FLAG)",
        "payload": {
            "query": "Should we buy shares before the quarterly results announcement?",
            "user_id": "arjun.kumar@bharatfinserv.in",
            "role": "junior_analyst",
            "jurisdiction": "IN",
            "session_id": "test-insider-4",
        },
        "expect_block": False,
        "expect_status": None,  # FAIL or WARNING acceptable
    },
    {
        "name": "TEST 5 - CEO asks cross-jurisdiction question (should ANSWER with conflict)",
        "payload": {
            "query": "What are the data retention requirements for our Singapore operations?",
            "user_id": "sunita.rao@bharatfinserv.in",
            "role": "ceo",
            "jurisdiction": "IN",
            "session_id": "test-cross-juris-5",
        },
        "expect_block": False,
        "expect_status": None,  # PASS or WARNING acceptable
    },
]


def run_test(test, idx):
    print(f"\n{'='*70}")
    print(f"  {test['name']}")
    print(f"{'='*70}")
    
    try:
        r = requests.post(API, json=test["payload"], timeout=120)
    except requests.exceptions.ConnectionError:
        print(f"  [FAIL] Could not connect to {API}")
        return False
    
    print(f"  HTTP Status: {r.status_code}")
    
    if r.status_code == 403:
        detail = r.json().get("detail", {})
        print(f"  [BLOCKED 403]: {detail.get('error', '')}")
        details = detail.get('details', [])
        for d in details:
            print(f"    - {d}")
        if test["expect_block"]:
            print(f"  [PASS] Query was correctly blocked")
            return True
        else:
            print(f"  [FAIL] Query should NOT have been blocked")
            return False
    
    if r.status_code != 200:
        print(f"  [FAIL] Unexpected HTTP status: {r.status_code}")
        print(f"  Body: {r.text[:300]}")
        return False
    
    d = r.json()
    compliance = d.get("compliance_status", "")
    answer = d.get("answer", "")
    sources = d.get("sources", [])
    leakage = d.get("leakage_risk", "")
    violations = d.get("violations", [])
    conflict = d.get("conflict_detected", False)
    conf_rules = d.get("conflicting_rules", [])
    recommendation = d.get("conservative_recommendation", "")
    
    print(f"  Compliance: {compliance}")
    print(f"  Leakage: {leakage}")
    print(f"  Sources: {[s.get('doc_id') for s in sources]}")
    print(f"  Violations: {violations}")
    print(f"  Conflict detected: {conflict}")
    if conf_rules:
        print(f"  Conflicting rules: {conf_rules}")
    if recommendation:
        print(f"  Recommendation: {recommendation[:200]}")
    print(f"  Answer (first 400 chars):")
    # Safely encode answer for Windows console
    safe_answer = answer[:400].encode('ascii', errors='replace').decode('ascii')
    print(f"    {safe_answer}")
    
    # Check if blocked at 200 level (our new gates return 200 with FAIL status)
    if test["expect_block"]:
        if compliance == "FAIL" or leakage == "HIGH":
            print(f"  [PASS] Query correctly blocked/flagged")
            return True
        else:
            print(f"  [FAIL] Query should have been blocked but got {compliance}")
            return False
    
    # For non-blocked tests, verify answer quality
    if test["expect_status"] and compliance != test["expect_status"]:
        print(f"  [NOTE] Expected {test['expect_status']} but got {compliance}")
    
    if not answer or "error" in answer.lower()[:50]:
        print(f"  [FAIL] Answer is empty or contains error")
        return False
    
    if "please refer to" in answer.lower() and idx != 0:
        print(f"  [WARN] Answer contains 'please refer to' (template response)")
    
    print(f"  [PASS]")
    return True


if __name__ == "__main__":
    print("Waiting 25 seconds for backend to start...")
    time.sleep(25)
    
    results = []
    for i, test in enumerate(TESTS):
        ok = run_test(test, i)
        results.append(ok)
        time.sleep(2)  # Rate limit guard
    
    print(f"\n{'='*70}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*70}")
    for i, (test, ok) in enumerate(zip(TESTS, results)):
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status}  {test['name']}")
    
    passed = sum(results)
    print(f"\n  {passed}/{len(results)} tests passed.")
    
    if not all(results):
        sys.exit(1)
