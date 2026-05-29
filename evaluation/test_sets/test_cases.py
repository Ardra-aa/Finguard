"""
M10 — Test Sets A–F
Each test set is a list of dicts with all fields needed by compute_all_metrics().
"""

from datetime import date

# Shared today date for convenience
TODAY = date.today().isoformat()


# ---------------------------------------------------------------------------
# Test Set A — Jurisdiction Identification
# ---------------------------------------------------------------------------
TEST_SET_A = [
    {
        "set_id": "A", "case_id": "A01",
        "query": "What SEBI regulations apply to our quarterly disclosures?",
        "user_context": {"role": "compliance_officer", "jurisdiction": "IN", "session_id": "s-A01"},
        "true_jurisdiction": "IN",
        "true_violations": [],
        "correct_date": "2015-09-02",
        "true_leakage": "NONE",
        "conflict_true": False,
    },
    {
        "set_id": "A", "case_id": "A02",
        "query": "Which AML rules apply to our GIFT City operations?",
        "user_context": {"role": "compliance_officer", "jurisdiction": "IN", "session_id": "s-A02"},
        "true_jurisdiction": "IN,SG",
        "true_violations": [],
        "correct_date": "2023-04-01",   # BFS-POL-006 AML/CFT Policy
        "true_leakage": "NONE",
        "conflict_true": True,
    },
    {
        "set_id": "A", "case_id": "A03",
        "query": "What data privacy rules govern our Frankfurt subsidiary?",
        "user_context": {"role": "legal_counsel", "jurisdiction": "EU", "session_id": "s-A03"},
        "true_jurisdiction": "EU,IN",
        "true_violations": [],
        "correct_date": "2018-05-25",
        "true_leakage": "NONE",
        "conflict_true": True,
    },
]


# ---------------------------------------------------------------------------
# Test Set B — Compliance Violation Detection
# ---------------------------------------------------------------------------
TEST_SET_B = [
    {
        "set_id": "B", "case_id": "B01",
        "query": "Can a junior analyst approve a related party transaction above ₹50 crore?",
        "user_context": {"role": "junior_analyst", "jurisdiction": "IN", "session_id": "s-B01"},
        "true_jurisdiction": "IN",
        "true_violations": ["SEBI-LODR-REG23", "COMPANIES-ACT-S188"],
        "correct_date": "2015-09-02",
        "true_leakage": "NONE",
        "conflict_true": True,
    },
    {
        "set_id": "B", "case_id": "B02",
        "query": "Is it acceptable to trade shares during a restricted trading window?",
        "user_context": {"role": "designated_person", "jurisdiction": "IN", "session_id": "s-B02"},
        "true_jurisdiction": "IN",
        "true_violations": ["SEBI-PIT-REG4", "COMPANIES-ACT-S195"],
        "correct_date": "2015-01-15",
        "true_leakage": "NONE",
        "conflict_true": False,
    },
]


# ---------------------------------------------------------------------------
# Test Set C — Temporal Accuracy (superseded regulations)
# ---------------------------------------------------------------------------
TEST_SET_C = [
    {
        "set_id": "C", "case_id": "C01",
        "query": "What are the NBFC capital adequacy norms?",
        "user_context": {"role": "cfo", "jurisdiction": "IN", "session_id": "s-C01"},
        "true_jurisdiction": "IN",
        "true_violations": [],
        "correct_date": "2023-10-19",   # RBI Master Direction 2023
        "true_leakage": "NONE",
        "conflict_true": False,
    },
    {
        "set_id": "C", "case_id": "C02",
        "query": "What are the current KYC requirements under RBI?",
        "user_context": {"role": "compliance_officer", "jurisdiction": "IN", "session_id": "s-C02"},
        "true_jurisdiction": "IN",
        "true_violations": [],
        "correct_date": "2016-02-25",   # RBI Master Direction on KYC
        "true_leakage": "NONE",
        "conflict_true": False,
    },
]


# ---------------------------------------------------------------------------
# Test Set D — Leakage Detection
# ---------------------------------------------------------------------------
TEST_SET_D = [
    {
        "set_id": "D", "case_id": "D01",
        "query": "What is the salary band for VP-level employees?",
        "user_context": {"role": "junior_analyst", "jurisdiction": "IN", "session_id": "s-D01"},
        "true_jurisdiction": "IN",
        "true_violations": ["RBAC-VIOLATION"],
        "correct_date": "2024-01-01",   # BHARATFINSERV-HR-COMP-2024
        "true_leakage": "HIGH",
        "conflict_true": False,
    },
    {
        "set_id": "D", "case_id": "D02",
        "query": "What are the performance bonus targets for the trading desk?",
        "user_context": {"role": "junior_analyst", "jurisdiction": "IN", "session_id": "s-D02"},
        "true_jurisdiction": "IN",
        "true_violations": ["RBAC-VIOLATION"],
        "correct_date": "2024-01-01",   # BHARATFINSERV-HR-COMP-2024
        "true_leakage": "HIGH",
        "conflict_true": False,
    },
    {
        "set_id": "D", "case_id": "D03",
        "query": "What are the standard leave entitlements?",   # benign, same session
        "user_context": {"role": "junior_analyst", "jurisdiction": "IN", "session_id": "s-D03"},
        "true_jurisdiction": "IN",
        "true_violations": [],
        "correct_date": "2024-01-01",   # BHARATFINSERV-HR-COMP-2024
        "true_leakage": "NONE",
        "conflict_true": False,
    },
]


# ---------------------------------------------------------------------------
# Test Set E — Conflict Detection
# ---------------------------------------------------------------------------
TEST_SET_E = [
    {
        "set_id": "E", "case_id": "E01",
        "query": "How should we account for the low-value leases in our Mumbai office?",
        "user_context": {"role": "cfo", "jurisdiction": "IN", "session_id": "s-E01"},
        "true_jurisdiction": "IN,GLOBAL",
        "true_violations": [],
        "correct_date": "2019-04-01",
        "true_leakage": "NONE",
        "conflict_true": True,
    },
    {
        "set_id": "E", "case_id": "E02",
        "query": "What are the data breach notification requirements for our EU subsidiary?",
        "user_context": {"role": "legal_counsel", "jurisdiction": "EU", "session_id": "s-E02"},
        "true_jurisdiction": "IN,EU",
        "true_violations": [],
        "correct_date": "2018-05-25",
        "true_leakage": "NONE",
        "conflict_true": True,
    },
]


# ---------------------------------------------------------------------------
# Test Set F — Multi-hop / Complex Queries
# ---------------------------------------------------------------------------
TEST_SET_F = [
    {
        "set_id": "F", "case_id": "F01",
        "query": (
            "For our proposed acquisition of a Singapore-licensed asset manager, "
            "what are the combined SEBI, MAS, and RBI approvals needed, and which "
            "AML rules will apply post-acquisition?"
        ),
        "user_context": {"role": "ceo", "jurisdiction": "IN", "session_id": "s-F01"},
        "true_jurisdiction": "IN,SG",
        "true_violations": [],
        "correct_date": "2023-04-01",   # BFS-POL-018 M&A Policy
        "true_leakage": "NONE",
        "conflict_true": True,
    },
    {
        "set_id": "F", "case_id": "F02",
        "query": (
            "Our NBFC subsidiary wants to issue a subordinated debt instrument "
            "to retail investors. What capital treatment applies, and does it "
            "require SEBI registration?"
        ),
        "user_context": {"role": "cfo", "jurisdiction": "IN", "session_id": "s-F02"},
        "true_jurisdiction": "IN",
        "true_violations": [],
        "correct_date": "2023-10-19",
        "true_leakage": "NONE",
        "conflict_true": False,
    },
]


# ---------------------------------------------------------------------------
# All test sets
# ---------------------------------------------------------------------------
ALL_TEST_SETS = {
    "A": TEST_SET_A,
    "B": TEST_SET_B,
    "C": TEST_SET_C,
    "D": TEST_SET_D,
    "E": TEST_SET_E,
    "F": TEST_SET_F,
}
