"""
tests/test_mock_contract.py
Verifies the mock_mode contract that the rest of the team depends on.
"""
import sys
from pathlib import Path
from datetime import date
from dataclasses import fields

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Finguard_rag.retrieval.interface import retrieve
from Finguard_rag.schemas.document_schema import UserContext, RankedDocument, FinancialDocument

ctx = UserContext(
    user_id='arjun.kumar@bharatfinserv.in',
    role='junior_analyst',
    jurisdiction='IN',
    reference_date=date.today(),
    session_id='test-session-001',
)

results = retrieve('KYC requirements', ctx, mock_mode=True)

# --- Check 1: Exactly 3 results ---
assert len(results) == 3, f"Expected 3, got {len(results)}"
print(f"[PASS] Exactly 3 RankedDocument objects returned")

# --- Check 2: All are RankedDocument ---
assert all(isinstance(r, RankedDocument) for r in results)
print(f"[PASS] All results are RankedDocument instances")

# --- Check 3: All contain FinancialDocument ---
assert all(isinstance(r.document, FinancialDocument) for r in results)
print(f"[PASS] All .document fields are FinancialDocument instances")

# --- Check 4: Field types on every result ---
for i, r in enumerate(results):
    d = r.document
    assert isinstance(d.doc_id, str) and d.doc_id, f"Result {i}: doc_id not a non-empty str"
    assert isinstance(d.content, str) and d.content, f"Result {i}: content not a non-empty str"
    assert isinstance(d.jurisdiction, str), f"Result {i}: jurisdiction not str"
    assert isinstance(d.valid_roles, list), f"Result {i}: valid_roles not list"
    assert all(isinstance(role, str) for role in d.valid_roles), f"Result {i}: valid_roles contains non-str"
    assert isinstance(d.effective_date, date), f"Result {i}: effective_date not a date object, got {type(d.effective_date)}"
    assert d.superseded_date is None or isinstance(d.superseded_date, date), f"Result {i}: superseded_date invalid"
    assert isinstance(d.risk_score, float), f"Result {i}: risk_score not float, got {type(d.risk_score)}"
    assert isinstance(d.risk_level, str), f"Result {i}: risk_level not str"
    assert isinstance(d.version, str), f"Result {i}: version not str"
    assert isinstance(d.source_file, str), f"Result {i}: source_file not str"
    assert isinstance(r.semantic_score, float), f"Result {i}: semantic_score not float"
    assert isinstance(r.final_score, float), f"Result {i}: final_score not float"
    assert isinstance(r.risk_score, float), f"Result {i}: risk_score not float"
print(f"[PASS] All field types validated on all 3 results")

# --- Check 5: Descending order ---
for i in range(len(results) - 1):
    assert results[i].final_score >= results[i+1].final_score
print(f"[PASS] Results sorted by final_score descending")

# --- Full structure of first result ---
r0 = results[0]
d0 = r0.document
print(f"\n{'='*60}")
print(f"  FIRST MOCK RESULT — Full Structure")
print(f"{'='*60}")
print(f"  RankedDocument:")
print(f"    semantic_score : {r0.semantic_score}  (float)")
print(f"    risk_score     : {r0.risk_score}  (float)")
print(f"    final_score    : {r0.final_score}  (float)")
print(f"    document       : FinancialDocument")
print(f"      doc_id          : {d0.doc_id!r}  (str)")
print(f"      content         : {d0.content!r}  (str)")
print(f"      jurisdiction    : {d0.jurisdiction!r}  (str)")
print(f"      regulatory_scope: {d0.regulatory_scope!r}  (str)")
print(f"      valid_roles     : {d0.valid_roles}  (List[str])")
print(f"      effective_date  : {d0.effective_date}  ({type(d0.effective_date).__name__})")
print(f"      superseded_date : {d0.superseded_date}  ({type(d0.superseded_date).__name__})")
print(f"      version         : {d0.version!r}  (str)")
print(f"      risk_level      : {d0.risk_level!r}  (str)")
print(f"      risk_score      : {d0.risk_score}  (float)")
print(f"      source_file     : {d0.source_file!r}  (str)")
print(f"      source_url      : {d0.source_url}  ({type(d0.source_url).__name__})")
print(f"      embedding       : {d0.embedding}  ({type(d0.embedding).__name__})")
print(f"\n{'='*60}")
print(f"  ALL 5 CHECKS PASSED — mock_mode contract verified")
print(f"{'='*60}")
