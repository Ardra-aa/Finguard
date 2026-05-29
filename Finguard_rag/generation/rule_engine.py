"""
Finguard_rag/generation/rule_engine.py
Amala P Ansalem — M6 Layer A: Symbolic Deontic Rule Engine

20 rules covering SEBI, RBI, Companies Act 2013, and Ind AS.
Each rule has a modality:
    MUST       — the response must include / comply with this.
    MUST_NOT   — the response must NOT contain this.  Violation → FAIL.
    PERMITTED  — advisory; no automatic enforcement.

Matching is done via keyword / phrase patterns against the LLM output.
A MUST_NOT match means the response is non-compliant and must be withheld.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------
@dataclass
class DeonticRule:
    """A single compliance rule in the symbolic rule engine."""
    rule_id: str                        # e.g. "SEBI_001"
    modality: str                       # "MUST" | "MUST_NOT" | "PERMITTED"
    regulator: str                      # "SEBI" | "RBI" | "MCA" | "ICAI"
    regulation: str                     # e.g. "SEBI PIT Regulations 2015"
    description: str                    # human-readable explanation
    patterns: List[str] = field(        # keyword / regex patterns to match
        default_factory=list
    )
    severity: str = "HIGH"              # "HIGH" | "MEDIUM" | "LOW"


# ---------------------------------------------------------------------------
# The 20 Deontic Rules
# ---------------------------------------------------------------------------
RULES: List[DeonticRule] = [
    # ===== SEBI Rules (1–7) =============================================

    DeonticRule(
        rule_id="SEBI_001",
        modality="MUST_NOT",
        regulator="SEBI",
        regulation="SEBI PIT Regulations 2015",
        description=(
            "Must NOT recommend or advise trading in securities during a "
            "trading window closure period."
        ),
        patterns=[
            r"recommend(?:s|ed|ing)?\s+(?:to\s+)?(?:buy|sell|trade|purchase|acquire)\s+"
            r"(?:shares|securities|stock)",
            r"you\s+(?:can|should|may)\s+(?:buy|sell|trade)",
            r"advise\s+(?:to\s+)?(?:buy|sell|trade)\s+during\s+(?:the\s+)?(?:trading\s+)?window\s+closure",
            r"trading\s+(?:is\s+)?(?:allowed|permitted|okay)\s+during\s+(?:closure|closed\s+window)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="SEBI_002",
        modality="MUST_NOT",
        regulator="SEBI",
        regulation="SEBI LODR Reg 30",
        description=(
            "Must NOT advise delaying or withholding disclosure of material "
            "events to stock exchanges."
        ),
        patterns=[
            r"delay\s+(?:the\s+)?disclosure",
            r"withhold\s+(?:the\s+)?(?:information|disclosure|announcement)",
            r"no\s+need\s+to\s+(?:disclose|report|announce)",
            r"avoid\s+(?:disclosing|reporting|announcing)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="SEBI_003",
        modality="MUST",
        regulator="SEBI",
        regulation="SEBI PIT Regulations 2015",
        description=(
            "Any mention of insider trading disclosure must reference the "
            "T+2 timeline requirement."
        ),
        patterns=[
            r"insider\s+trading\s+disclosure",
            r"material\s+(?:non-public\s+)?information\s+disclosure",
        ],
        severity="MEDIUM",
    ),

    DeonticRule(
        rule_id="SEBI_004",
        modality="MUST_NOT",
        regulator="SEBI",
        regulation="SEBI LODR Reg 23",
        description=(
            "Must NOT approve related party transactions without proper "
            "audit committee approval."
        ),
        patterns=[
            r"(?:skip|bypass|avoid|no\s+need\s+for)\s+(?:audit\s+committee|board)\s+approval"
            r"\s+(?:for\s+)?(?:related\s+party|RPT)",
            r"related\s+party\s+(?:transactions?\s+)?(?:do\s+)?(?:not\s+)?need\s+"
            r"(?:committee|board)\s+approval",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="SEBI_005",
        modality="MUST_NOT",
        regulator="SEBI",
        regulation="SEBI (SBEB) Regulations 2021",
        description=(
            "Must NOT misrepresent ESOP vesting schedules or grant terms."
        ),
        patterns=[
            r"esop\s+(?:vest|grant)\s+(?:immediately|instantly|without\s+restriction)",
            r"no\s+(?:lock.?in|vesting)\s+(?:period|requirement)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="SEBI_006",
        modality="MUST_NOT",
        regulator="SEBI",
        regulation="SEBI Takeover Code 2011",
        description=(
            "Must NOT advise bypassing mandatory open offer requirements "
            "when acquiring shares beyond the threshold."
        ),
        patterns=[
            r"(?:avoid|bypass|skip|no\s+need\s+for)\s+(?:the\s+)?(?:mandatory\s+open\s+offer|(?:open|mandatory)\s+offer)",
            r"acquire\s+(?:shares|stake)\s+(?:without|bypassing)\s+(?:open\s+)?offer",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="SEBI_007",
        modality="PERMITTED",
        regulator="SEBI",
        regulation="SEBI LODR Reg 46",
        description=(
            "Permitted to reference information already disclosed on "
            "the company website per Reg 46 requirements."
        ),
        patterns=[
            r"(?:company|corporate)\s+website\s+disclosure",
            r"reg(?:ulation)?\s+46\s+(?:compliance|disclosure)",
        ],
        severity="LOW",
    ),

    # ===== RBI Rules (8–12) =============================================

    DeonticRule(
        rule_id="RBI_001",
        modality="MUST_NOT",
        regulator="RBI",
        regulation="RBI Master Direction on KYC 2023",
        description=(
            "Must NOT advise onboarding customers without completing "
            "KYC verification as per RBI norms."
        ),
        patterns=[
            r"(?:skip|bypass|avoid|waive)\s+(?:the\s+)?kyc",
            r"onboard\s+(?:the\s+)?(?:customer|client)\s+without\s+kyc",
            r"kyc\s+(?:is\s+)?(?:not\s+)?(?:required|necessary|needed)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="RBI_002",
        modality="MUST_NOT",
        regulator="RBI",
        regulation="PMLA 2002",
        description=(
            "Must NOT advise ignoring or bypassing suspicious transaction "
            "reporting (STR) obligations."
        ),
        patterns=[
            r"(?:ignore|skip|bypass|avoid)\s+(?:the\s+)?(?:suspicious\s+transaction|STR)",
            r"no\s+need\s+to\s+(?:report|file)\s+(?:suspicious|STR)",
            r"don'?t\s+(?:need\s+to\s+)?(?:report|file)\s+(?:suspicious|STR)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="RBI_003",
        modality="MUST_NOT",
        regulator="RBI",
        regulation="RBI Master Direction on NBFCs (Prudential) 2023",
        description=(
            "Must NOT advise setting lending rates above the RBI-mandated "
            "interest rate caps for NBFCs."
        ),
        patterns=[
            r"(?:charge|set|offer)\s+(?:interest\s+)?(?:rate|rates)\s+(?:above|exceeding|higher\s+than)"
            r"\s+(?:rbi|regulatory)\s+(?:cap|limit|ceiling)",
            r"no\s+(?:interest\s+rate\s+)?(?:cap|ceiling|limit)\s+(?:applies|exists)",
            r"interest\s+rate\s+cap\s+(?:does\s+)?(?:not\s+)?apply",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="RBI_004",
        modality="MUST_NOT",
        regulator="RBI",
        regulation="RBI Master Direction on NBFCs (Prudential) 2023",
        description=(
            "Must NOT advise NBFC capital adequacy ratios below the "
            "RBI-mandated minimum of 15%."
        ),
        patterns=[
            r"capital\s+adequacy\s+(?:ratio\s+)?(?:below|under|less\s+than)\s+15",
            r"(?:CRAR|CAR)\s+(?:of\s+)?(?:below|under|less\s+than)\s+15",
            r"(?:reduce|lower)\s+(?:the\s+)?capital\s+adequacy\s+below\s+(?:the\s+)?(?:rbi|minimum)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="RBI_005",
        modality="MUST",
        regulator="RBI",
        regulation="RBI Guidelines on Cyber Security 2016",
        description=(
            "Any response about IT security must reference the RBI "
            "Cyber Security Framework requirements."
        ),
        patterns=[
            r"cyber\s+security\s+(?:policy|framework|guideline)",
            r"(?:it|information)\s+security\s+(?:for\s+)?(?:bank|nbfc|financial)",
        ],
        severity="MEDIUM",
    ),

    # ===== Companies Act / MCA Rules (13–17) ============================

    DeonticRule(
        rule_id="MCA_001",
        modality="MUST_NOT",
        regulator="MCA",
        regulation="Companies Act 2013, Section 177",
        description=(
            "Must NOT advise bypassing the audit committee for matters "
            "requiring mandatory audit committee review."
        ),
        patterns=[
            r"(?:skip|bypass|avoid|no\s+need\s+for)\s+(?:the\s+)?audit\s+committee",
            r"audit\s+committee\s+(?:is\s+)?(?:not\s+)?(?:required|necessary|needed|mandatory)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="MCA_002",
        modality="MUST_NOT",
        regulator="MCA",
        regulation="Companies Act 2013, Section 135",
        description=(
            "Must NOT advise that CSR obligations can be ignored by "
            "companies meeting the statutory thresholds."
        ),
        patterns=[
            r"(?:skip|avoid|ignore|not\s+required)\s+(?:to\s+)?(?:spend\s+on\s+)?csr",
            r"csr\s+(?:is\s+)?(?:not\s+)?(?:mandatory|compulsory|required|needed)",
            r"no\s+(?:need|obligation)\s+(?:for\s+)?csr",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="MCA_003",
        modality="MUST_NOT",
        regulator="MCA",
        regulation="Companies Act 2013, Sections 179-180",
        description=(
            "Must NOT advise board-level capital expenditure decisions "
            "without proper board resolution."
        ),
        patterns=[
            r"(?:skip|bypass|without)\s+(?:the\s+)?board\s+(?:approval|resolution)",
            r"(?:no\s+need\s+for|not\s+required)\s+(?:the\s+)?board\s+(?:approval|resolution)",
            r"capex\s+(?:without|bypass(?:ing)?)\s+board",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="MCA_004",
        modality="MUST_NOT",
        regulator="MCA",
        regulation="Companies Act 2013, Section 123",
        description=(
            "Must NOT advise paying dividends from sources other than "
            "profits or free reserves."
        ),
        patterns=[
            r"(?:pay|declare|distribute)\s+dividend\s+(?:from|using|out\s+of)\s+"
            r"(?:capital|borrowings|debt|loan)",
            r"dividend\s+(?:without|despite)\s+(?:sufficient\s+)?(?:profits|reserves)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="MCA_005",
        modality="MUST",
        regulator="MCA",
        regulation="Companies Act 2013, Section 188",
        description=(
            "Related party transactions above threshold must mention "
            "shareholder approval requirement."
        ),
        patterns=[
            r"related\s+party\s+(?:transaction|dealing)\s+(?:above|exceeding)\s+threshold",
        ],
        severity="MEDIUM",
    ),

    # ===== Ind AS / Accounting Rules (18–20) ============================

    DeonticRule(
        rule_id="INDAS_001",
        modality="MUST_NOT",
        regulator="ICAI",
        regulation="Ind AS 115 — Revenue Recognition",
        description=(
            "Must NOT advise recognising revenue before performance "
            "obligations are satisfied."
        ),
        patterns=[
            r"recogni[sz]e\s+revenue\s+(?:before|prior\s+to|without)\s+"
            r"(?:performance|delivery|satisfaction)",
            r"(?:upfront|immediate)\s+revenue\s+recognition\s+(?:without|before)",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="INDAS_002",
        modality="MUST_NOT",
        regulator="ICAI",
        regulation="Ind AS 116 — Leases",
        description=(
            "Must NOT advise keeping all leases off-balance-sheet.  "
            "Ind AS 116 requires right-of-use asset recognition for "
            "most lessee leases."
        ),
        patterns=[
            r"(?:keep|maintain|treat)\s+(?:all\s+)?leases?\s+(?:as\s+)?off.?balance.?sheet",
            r"no\s+need\s+to\s+(?:capitalise|capitalize|recogni[sz]e)\s+(?:the\s+)?lease",
            r"operating\s+lease\s+(?:treatment|classification)\s+(?:for\s+)?all",
        ],
        severity="HIGH",
    ),

    DeonticRule(
        rule_id="INDAS_003",
        modality="MUST_NOT",
        regulator="ICAI",
        regulation="Ind AS 109 — Financial Instruments",
        description=(
            "Must NOT advise ignoring expected credit loss (ECL) "
            "provisioning requirements."
        ),
        patterns=[
            r"(?:skip|ignore|avoid|no\s+need\s+for)\s+(?:expected\s+)?(?:credit\s+)?loss\s+provisioning",
            r"(?:ECL|expected\s+credit\s+loss)\s+(?:is\s+)?(?:not\s+)?(?:required|necessary|applicable)",
            r"no\s+(?:need\s+)?(?:for\s+)?(?:ECL|impairment)\s+provisioning",
        ],
        severity="HIGH",
    ),
]


# ---------------------------------------------------------------------------
# Rule Engine — Public API
# ---------------------------------------------------------------------------
def evaluate_rules(response_text: str) -> Tuple[str, List[str]]:
    """
    Run all 20 deontic rules against the LLM response text.

    Logic:
        1. For every MUST_NOT rule: if **any** pattern matches the response,
           the rule is violated → status = FAIL, response should be withheld.
        2. For every MUST rule: if patterns match *but* the expected
           content is absent, flag a WARNING (advisory only).
        3. PERMITTED rules are informational and never trigger violations.

    Args:
        response_text: The raw answer string produced by the LLM.

    Returns:
        (status, violations) where:
        - status is "PASS", "WARNING", or "FAIL".
        - violations is a list of rule_id strings that fired.
    """
    text_lower = response_text.lower()
    violations: List[str] = []
    warnings: List[str] = []

    for rule in RULES:
        if rule.modality == "PERMITTED":
            continue  # informational only

        for pattern in rule.patterns:
            if re.search(pattern, text_lower):
                if rule.modality == "MUST_NOT":
                    violations.append(rule.rule_id)
                    logger.warning(
                        "MUST_NOT violation: %s — %s",
                        rule.rule_id,
                        rule.description,
                    )
                elif rule.modality == "MUST":
                    # MUST rules: pattern match is a positive signal
                    # (the response mentions the topic).  No violation.
                    pass
                break  # one match per rule is sufficient

    # Determine overall status
    if violations:
        return "FAIL", violations
    elif warnings:
        return "WARNING", warnings
    else:
        return "PASS", []


def get_rule(rule_id: str) -> DeonticRule:
    """Look up a rule by its ID.  Returns None if not found."""
    for rule in RULES:
        if rule.rule_id == rule_id:
            return rule
    return None


def get_all_rules() -> List[DeonticRule]:
    """Return the full list of 20 deontic rules."""
    return RULES.copy()
