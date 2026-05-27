"""
Finguard_rag/generation/compliance_validator.py
Amala P Ansalem — M6: Compliance Validation Orchestrator

Orchestrates both validation layers and returns a combined result:

    Layer A (Symbolic):  rule_engine.evaluate_rules()
        20 deontic rules — MUST_NOT violation → FAIL (response withheld)

    Layer B (Neural):    safety_classifier.classify_safety()
        Cosine similarity to known-bad patterns — score ≥ 0.82 → WARNING

Combined logic:
    - Any MUST_NOT violation         →  status = FAIL
    - Neural flag (no MUST_NOT)      →  status = WARNING
    - Neither                        →  status = PASS

When status is FAIL, the answer text is replaced with a safe refusal
message and the original answer is NOT returned to the user.
"""

import sys
import logging
from typing import Dict, List
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Finguard_rag.schemas.document_schema import RankedDocument, UserContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load config flags
# ---------------------------------------------------------------------------
_CONFIG_PATH = _REPO_ROOT / "config.yaml"


def _load_compliance_config() -> Dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("compliance", {})
    return {
        "enable_symbolic_rules": True,
        "enable_neural_safety": True,
        "noncompliant_pattern_threshold": 0.82,
    }


_COMPLIANCE_CFG = _load_compliance_config()

# ---------------------------------------------------------------------------
# Refusal message when a FAIL is detected
# ---------------------------------------------------------------------------
REFUSAL_MESSAGE = (
    "[FinGuard Compliance Gate — Response Withheld]\n\n"
    "The generated response was found to violate one or more mandatory "
    "compliance rules and has been withheld to protect BharatFinServ Ltd. "
    "from regulatory risk.\n\n"
    "Violated rule(s): {rule_ids}\n\n"
    "Please rephrase your query or contact the compliance team for assistance."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def validate(
    answer_text: str,
    docs: List[RankedDocument],
    user_context: UserContext,
    mock_mode: bool = False,
) -> Dict:
    """
    Run both compliance validation layers on the LLM response.

    This function is called by ``generation/interface.py`` after M5
    produces the raw answer text.

    Args:
        answer_text:  Raw LLM response string.
        docs:         The ranked documents that were used as context.
        user_context: Current user metadata.
        mock_mode:    If True, skip all checks and return PASS.

    Returns:
        A dict with keys:
            ``status``      (str):   "PASS" | "WARNING" | "FAIL"
            ``violations``  (list):  Rule IDs that fired (Layer A).
            ``neural_flags`` (list): Matched patterns from Layer B.
            ``confidence``  (float): Confidence score (1.0 = fully clean).
            ``withheld``    (bool):  True if the answer was replaced.
            ``safe_answer`` (str|None): Replacement answer text if withheld.
    """
    # ------------------------------------------------------------------ #
    # Mock mode — instant clean pass
    # ------------------------------------------------------------------ #
    if mock_mode:
        return {
            "status": "PASS",
            "violations": [],
            "neural_flags": [],
            "confidence": 0.95,
            "withheld": False,
            "safe_answer": None,
        }

    violations: List[str] = []
    neural_flags: List[Dict] = []
    status = "PASS"
    confidence = 1.0

    # ------------------------------------------------------------------ #
    # Layer A — Symbolic Deontic Rule Engine
    # ------------------------------------------------------------------ #
    if _COMPLIANCE_CFG.get("enable_symbolic_rules", True):
        from Finguard_rag.generation.rule_engine import evaluate_rules, get_rule

        rule_status, rule_violations = evaluate_rules(answer_text)

        if rule_violations:
            violations.extend(rule_violations)
            # Log which rules fired and their descriptions
            for rid in rule_violations:
                rule = get_rule(rid)
                if rule:
                    logger.warning(
                        "Layer A violation — %s [%s]: %s",
                        rid,
                        rule.modality,
                        rule.description,
                    )

        if rule_status == "FAIL":
            status = "FAIL"
            confidence = 0.0
        elif rule_status == "WARNING" and status != "FAIL":
            status = "WARNING"
            confidence = min(confidence, 0.6)

        logger.info(
            "Layer A (Symbolic): status=%s, violations=%d",
            rule_status,
            len(rule_violations),
        )

    # ------------------------------------------------------------------ #
    # Layer B — Neural Safety Classifier
    # ------------------------------------------------------------------ #
    if _COMPLIANCE_CFG.get("enable_neural_safety", True):
        from Finguard_rag.generation.safety_classifier import classify_safety

        safety_result = classify_safety(answer_text, mock_mode=False)

        if safety_result["flagged"]:
            neural_flags = safety_result["matches"]

            # Neural flag alone → WARNING (not FAIL)
            if status != "FAIL":
                status = "WARNING"

            # Adjust confidence based on max similarity score
            max_score = safety_result["max_score"]
            confidence = min(confidence, max(0.1, 1.0 - max_score))

            logger.warning(
                "Layer B (Neural): flagged=True, max_score=%.4f, matches=%d",
                max_score,
                len(neural_flags),
            )
        else:
            logger.info(
                "Layer B (Neural): flagged=False, max_score=%.4f",
                safety_result["max_score"],
            )

    # ------------------------------------------------------------------ #
    # If FAIL: prepare the safe refusal answer
    # ------------------------------------------------------------------ #
    withheld = status == "FAIL"
    safe_answer = None

    if withheld:
        rule_ids_str = ", ".join(violations) if violations else "unknown"
        safe_answer = REFUSAL_MESSAGE.format(rule_ids=rule_ids_str)
        logger.critical(
            "COMPLIANCE FAIL — response withheld.  Violations: %s",
            rule_ids_str,
        )

    return {
        "status": status,
        "violations": violations,
        "neural_flags": neural_flags,
        "confidence": round(confidence, 4),
        "withheld": withheld,
        "safe_answer": safe_answer,
    }
