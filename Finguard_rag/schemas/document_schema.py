# finguard_rag/schemas/document_schema.py
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date

@dataclass
class FinancialDocument:
    doc_id: str                     # e.g. "SEBI-LODR-2015-REG30"
    content: str                    # chunk text (512 tokens)
    jurisdiction: str               # "IN" | "SG" | "EU" | "GLOBAL"
    regulatory_scope: str           # "securities"|"banking"|"insurance"|"corporate"
    valid_roles: List[str]          # roles permitted to retrieve this chunk
    effective_date: date            # date from which this version is valid
    superseded_date: Optional[date] # date this version was replaced (None if current)
    version: str = "1.0"
    risk_level: str = "MEDIUM"      # "LOW" | "MEDIUM" | "HIGH"
    risk_score: float = 0.5         # 0.0 (safe) to 1.0 (high risk)
    source_file: str = ''
    source_url: Optional[str] = None
    embedding: Optional[List[float]] = None

@dataclass
class UserContext:
    user_id: str                    # e.g. "arjun.kumar@bharatfinserv.in"
    role: str                       # e.g. "junior_analyst"
    jurisdiction: str               # e.g. "IN"
    reference_date: date            # for temporal queries (default today)
    session_id: str                 # for leakage tracking

@dataclass
class RankedDocument:
    document: FinancialDocument
    semantic_score: float           # raw cosine similarity
    risk_score: float               # from document metadata
    final_score: float              # alpha*semantic - beta*risk

@dataclass
class ComplianceResponse:
    answer: str
    sources: List[FinancialDocument]
    compliance_status: str          # "PASS" | "WARNING" | "FAIL"
    violations: List[str]           # rule IDs that fired
    conflicts: List[str]            # jurisdiction conflict descriptions
    leakage_risk: str               # "NONE" | "LOW" | "HIGH"
    confidence_score: float
    agent_trace: Optional[List[dict]] = None  # [{type,content}]

@dataclass
class DefenseResult:
    leakage_risk: str               # "NONE" | "LOW" | "HIGH"
    leakage_details: List[str]
    conflict_detected: bool
    conflicting_rules: List[str]
    conservative_recommendation: str

@dataclass
class AgentResponse:
    final_response: ComplianceResponse
    agent_trace: List[dict]         # [{type: THINK|ACT|OBS, content: str}]
    total_iterations: int
