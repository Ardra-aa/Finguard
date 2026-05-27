"""
Finguard_rag/generation/noncompliant_patterns.py
Amala P Ansalem — M6 Layer B: Known Non-Compliant Response Patterns

A curated library of response fragments that are known to be non-compliant
in the Indian financial regulatory context.  The safety_classifier compares
the LLM output (sentence by sentence) against these patterns using cosine
similarity with sentence-transformers embeddings.

If any sentence in the LLM output has cosine similarity > 0.82 with any
pattern here, the response is flagged as WARNING.

Categories:
    1. Insider trading / market manipulation
    2. KYC / AML evasion
    3. Regulatory disclosure avoidance
    4. Accounting manipulation
    5. Corporate governance bypass
    6. Fiduciary duty violations
"""

from typing import List, Dict

# ---------------------------------------------------------------------------
# Each pattern has:
#   - text:     The non-compliant statement (will be embedded for comparison)
#   - category: Classification for logging / reporting
#   - severity: "HIGH" | "MEDIUM" — indicates how dangerous a match is
# ---------------------------------------------------------------------------
NONCOMPLIANT_PATTERNS: List[Dict[str, str]] = [

    # === 1. Insider Trading / Market Manipulation =========================
    {
        "text": "You can trade shares freely during the trading window closure period.",
        "category": "insider_trading",
        "severity": "HIGH",
    },
    {
        "text": "There is no need to report insider trading to SEBI.",
        "category": "insider_trading",
        "severity": "HIGH",
    },
    {
        "text": "It is acceptable to share unpublished price sensitive information "
                "with family members for personal investment decisions.",
        "category": "insider_trading",
        "severity": "HIGH",
    },
    {
        "text": "You may use confidential board meeting information to make "
                "investment decisions before the public announcement.",
        "category": "insider_trading",
        "severity": "HIGH",
    },

    # === 2. KYC / AML Evasion =============================================
    {
        "text": "KYC verification is optional for small-value customers.",
        "category": "kyc_aml_evasion",
        "severity": "HIGH",
    },
    {
        "text": "You do not need to file suspicious transaction reports for "
                "amounts below the threshold.",
        "category": "kyc_aml_evasion",
        "severity": "HIGH",
    },
    {
        "text": "Anti-money laundering checks can be skipped for trusted "
                "long-standing clients.",
        "category": "kyc_aml_evasion",
        "severity": "HIGH",
    },

    # === 3. Regulatory Disclosure Avoidance ================================
    {
        "text": "You can delay the disclosure of material events to the stock "
                "exchange until a more favourable time.",
        "category": "disclosure_avoidance",
        "severity": "HIGH",
    },
    {
        "text": "There is no obligation to disclose related party transactions "
                "if the board informally approves them.",
        "category": "disclosure_avoidance",
        "severity": "HIGH",
    },
    {
        "text": "The company does not need to inform shareholders about "
                "significant litigation or regulatory orders.",
        "category": "disclosure_avoidance",
        "severity": "HIGH",
    },

    # === 4. Accounting Manipulation ========================================
    {
        "text": "Revenue can be recognized immediately upon contract signing "
                "regardless of whether performance obligations are met.",
        "category": "accounting_manipulation",
        "severity": "HIGH",
    },
    {
        "text": "All leases can be treated as operating leases and kept "
                "off the balance sheet to improve financial ratios.",
        "category": "accounting_manipulation",
        "severity": "HIGH",
    },
    {
        "text": "Expected credit loss provisions are not necessary if the "
                "company believes the borrower will eventually repay.",
        "category": "accounting_manipulation",
        "severity": "HIGH",
    },
    {
        "text": "The company may pay dividends from borrowed funds if "
                "retained earnings are insufficient.",
        "category": "accounting_manipulation",
        "severity": "HIGH",
    },

    # === 5. Corporate Governance Bypass ====================================
    {
        "text": "Board approval is not required for capital expenditure "
                "decisions made by the management team.",
        "category": "governance_bypass",
        "severity": "HIGH",
    },
    {
        "text": "The audit committee review can be bypassed for routine "
                "related party transactions.",
        "category": "governance_bypass",
        "severity": "HIGH",
    },
    {
        "text": "CSR spending is voluntary and companies can choose not to "
                "spend the mandated 2% of net profits.",
        "category": "governance_bypass",
        "severity": "MEDIUM",
    },

    # === 6. Fiduciary Duty / Interest Rate Violations =====================
    {
        "text": "NBFCs can charge any interest rate they wish as there is "
                "no regulatory cap on lending rates.",
        "category": "fiduciary_violation",
        "severity": "HIGH",
    },
    {
        "text": "Capital adequacy requirements do not apply to smaller NBFCs.",
        "category": "fiduciary_violation",
        "severity": "HIGH",
    },
    {
        "text": "The NBFC can maintain a capital adequacy ratio below 15% "
                "if its asset quality is strong.",
        "category": "fiduciary_violation",
        "severity": "HIGH",
    },
]


def get_all_patterns() -> List[Dict[str, str]]:
    """Return the full list of non-compliant patterns."""
    return NONCOMPLIANT_PATTERNS.copy()


def get_pattern_texts() -> List[str]:
    """Return just the text strings (for embedding)."""
    return [p["text"] for p in NONCOMPLIANT_PATTERNS]


def get_patterns_by_category(category: str) -> List[Dict[str, str]]:
    """Filter patterns by category."""
    return [p for p in NONCOMPLIANT_PATTERNS if p["category"] == category]
