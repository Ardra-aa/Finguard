"""
M9 — Jurisdiction Conflict Ontology
Maps (jurisdiction_A, jurisdiction_B, topic) → known conflict patterns.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class ConflictPattern:
    jurisdiction_a: str
    jurisdiction_b: str
    topic: str
    description: str
    conservative_recommendation: str
    trigger_keywords: List[str]
    doc_id_hints: List[str]


CONFLICT_PATTERNS: List[ConflictPattern] = [

    ConflictPattern(
        jurisdiction_a="IN", jurisdiction_b="GLOBAL",
        topic="lease_accounting",
        description=(
            "Ind AS 116 (India) and IFRS 16 differ on the low-value asset practical "
            "expedient. Application thresholds and disclosures diverge for multinational "
            "consolidation."
        ),
        conservative_recommendation=(
            "Apply Ind AS 116 strictly for Indian entity statements. For consolidated IFRS "
            "reporting apply IFRS 16 without the low-value expedient unless confirmed by the "
            "group auditor. Disclose both treatments in the notes."
        ),
        trigger_keywords=["lease", "ind as 116", "ifrs 16", "low-value", "short-term lease",
                          "right-of-use", "operating lease", "finance lease"],
        doc_id_hints=["POL-011", "IndAS_Compendium", "IFRS16", "Ind_AS_116"],
    ),

    ConflictPattern(
        jurisdiction_a="IN", jurisdiction_b="GLOBAL",
        topic="insurance_contracts",
        description=(
            "Ind AS 104 and IFRS 17 diverge significantly. IFRS 17 requires the Building "
            "Block Approach (BBA) and Contractual Service Margin (CSM); Ind AS 104 does not."
        ),
        conservative_recommendation=(
            "Prepare dual-basis statements: Ind AS 104 for Indian statutory reporting and "
            "IFRS 17 for group consolidation. Engage the group auditor before applying any "
            "measurement model elections."
        ),
        trigger_keywords=["insurance", "ind as 104", "ifrs 17", "csm",
                          "contractual service margin", "bba", "building block",
                          "insurance contract", "premium allocation"],
        doc_id_hints=["IFRS17", "Ind_AS_104", "insurance"],
    ),

    ConflictPattern(
        jurisdiction_a="IN", jurisdiction_b="IN",
        topic="related_party_transactions",
        description=(
            "SEBI LODR Reg 23 and Companies Act Section 188 both govern RPTs but with "
            "different thresholds and approval mechanisms. A transaction may require "
            "shareholder approval under SEBI but only board approval under the Act."
        ),
        conservative_recommendation=(
            "Apply the more stringent approval requirement across both regulations. "
            "If SEBI LODR requires shareholder approval, obtain it even if Companies Act "
            "requires only board approval. Document analysis under both frameworks."
        ),
        trigger_keywords=["related party", "rpt", "section 188", "lodr reg 23",
                          "materiality threshold", "arm's length", "shareholder approval",
                          "audit committee"],
        doc_id_hints=["POL-007", "SEBI_LODR", "Companies_Act", "RPT", "Reg_23"],
    ),

    ConflictPattern(
        jurisdiction_a="IN", jurisdiction_b="SG",
        topic="aml_cft",
        description=(
            "PMLA 2002 (India) and MAS AML/CFT Guidelines (Singapore) both apply to GIFT "
            "City IFSC and cross-border Singapore operations. Beneficial ownership thresholds "
            "and STR timelines differ."
        ),
        conservative_recommendation=(
            "Apply MAS AML/CFT beneficial ownership threshold (25%) for all cross-border "
            "transactions through the GIFT City entity. Use the shorter of PMLA and MAS STR "
            "deadlines. Maintain dual STR filing capability."
        ),
        trigger_keywords=["aml", "cft", "anti-money laundering", "pmla", "suspicious transaction",
                          "str", "beneficial owner", "mas aml", "gift city", "ifsc",
                          "customer due diligence", "cdd"],
        doc_id_hints=["POL-006", "MAS_AML", "PMLA", "RBI_MD_KYC"],
    ),

    ConflictPattern(
        jurisdiction_a="IN", jurisdiction_b="IN",
        topic="insider_trading_disclosure",
        description=(
            "SEBI LODR Reg 30, SEBI PIT Regulations 2015, and Companies Act Section 195 "
            "each impose different timelines: LODR Reg 30 = T+24h for material events; "
            "PIT = T+2 trading days for designated person trades."
        ),
        conservative_recommendation=(
            "Disclose material events to exchanges within T+24h (LODR Reg 30). Disclose "
            "designated person trades within T+2 trading days (PIT). Maintain a Structured "
            "Digital Database (SDD) as required by SEBI PIT."
        ),
        trigger_keywords=["insider trading", "upsi", "trading window", "designated person",
                          "sebi pit", "lodr reg 30", "section 195", "disclosure", "t+2",
                          "structured digital database", "sdd"],
        doc_id_hints=["POL-004", "POL-009", "SEBI_PIT", "SEBI_LODR", "Companies_Act"],
    ),

    ConflictPattern(
        jurisdiction_a="IN", jurisdiction_b="SG",
        topic="capital_adequacy",
        description=(
            "RBI Master Direction on NBFCs (Prudential) 2023 and MAS Notice 637 both set "
            "capital adequacy requirements. Tier 1/Tier 2 definitions differ between RBI "
            "norms and IFSCA (MAS-aligned) norms for the GIFT City entity."
        ),
        conservative_recommendation=(
            "Apply the higher of the two applicable capital ratios for dual-jurisdiction "
            "entities. For GIFT City: apply IFSCA Banking Regulations 2020. For NBFC: "
            "apply RBI Master Direction 2023. Report on prescribed formats to both regulators."
        ),
        trigger_keywords=["capital adequacy", "tier 1", "tier 2", "crar", "rwa",
                          "risk weighted assets", "mas notice 637", "ifsca", "nbfc capital",
                          "rbi prudential", "capital ratio"],
        doc_id_hints=["POL-012", "POL-013", "RBI_MD_NBFC", "MAS_Notice637", "IFSCA_Banking"],
    ),

    ConflictPattern(
        jurisdiction_a="IN", jurisdiction_b="EU",
        topic="data_privacy",
        description=(
            "DPDPA 2023 (India) and GDPR (EU) both apply. GDPR requires 72h breach "
            "notification to supervisory authority; DPDPA requires 'intimation' without "
            "specifying a 72h deadline. Consent and data transfer standards also differ."
        ),
        conservative_recommendation=(
            "Apply GDPR 72h breach notification timeline globally. Apply GDPR consent "
            "standards as the baseline. For cross-border India→EU data transfers use "
            "Standard Contractual Clauses (SCCs) until DPDPA transfer rules are finalised."
        ),
        trigger_keywords=["gdpr", "data privacy", "personal data", "data breach",
                          "breach notification", "dpdpa", "consent", "data protection",
                          "data subject", "controller", "processor"],
        doc_id_hints=["POL-002", "GDPR", "DPDPA", "Data_Retention"],
    ),
]


def get_all_patterns() -> List[ConflictPattern]:
    return CONFLICT_PATTERNS
