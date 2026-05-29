"""
M11 — FastAPI Request/Response Models
"""
from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class QueryRequest(BaseModel):
    query: str
    user_id: str
    role: str
    jurisdiction: str = "IN"
    session_id: str
    reference_date: Optional[date] = None
    mock_mode: bool = False


class SourceDoc(BaseModel):
    doc_id: str
    content: str
    jurisdiction: str
    regulatory_scope: str
    risk_level: str
    effective_date: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]
    compliance_status: str           # "PASS" | "WARNING" | "FAIL"
    violations: list                     # rule IDs (str) or violation dicts
    conflicts: list
    leakage_risk: str                # "NONE" | "LOW" | "HIGH"
    leakage_details: List[str]
    conflict_detected: bool
    conflicting_rules: List[str]
    conservative_recommendation: str
    confidence_score: float
    agent_trace: Optional[List[dict]] = None


class LeakageReport(BaseModel):
    session_id: str
    user_id: str
    role: str
    query_count: int
    leakage_risk: str
    alerts: List[str]
    queries: List[dict]


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"


class SessionSummary(BaseModel):
    session_id: str
    user_id: str
    role: str
    query_count: int
    leakage_risk: str
    alerts: List[str]
    created_at: str
