"""
M10 — Evaluation Metrics
Implements all 7 metrics from the FinGuard-RAG evaluation framework.

Metrics:
    JC   — Jurisdiction Correctness
    CVR  — Compliance Violation Rate
    TA   — Temporal Accuracy
    LDR  — Leakage Detection Rate
    CDR  — Conflict Detection Rate
    F    — Faithfulness (answer grounded in sources)
    LAT  — Latency (seconds per query)
"""

from __future__ import annotations
from typing import List, Dict, Any


# ---------------------------------------------------------------------------
# Individual metric functions
# ---------------------------------------------------------------------------

def jurisdiction_correctness(predictions: List[str], ground_truths: List[str]) -> float:
    """
    JC = fraction of responses that correctly identify the applicable jurisdiction(s).
    Both lists are sets of jurisdiction codes e.g. ["IN", "SG"].
    """
    if not predictions:
        return 0.0
    correct = sum(
        1 for p, g in zip(predictions, ground_truths)
        if set(p.split(",")) == set(g.split(","))
    )
    return correct / len(predictions)


def compliance_violation_rate(
    detected_violations: List[List[str]],
    true_violations: List[List[str]],
) -> Dict[str, float]:
    """
    CVR — precision and recall over detected compliance violations.
    Each element is a list of rule IDs.
    """
    tp = fp = fn = 0
    for det, true in zip(detected_violations, true_violations):
        det_set, true_set = set(det), set(true)
        tp += len(det_set & true_set)
        fp += len(det_set - true_set)
        fn += len(true_set - det_set)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) else 0.0)
    return {"precision": precision, "recall": recall, "f1": f1}


def temporal_accuracy(
    response_dates: List[str],
    correct_effective_dates: List[str],
) -> float:
    """
    TA = fraction of responses citing the correct effective/superseded date.
    Dates as ISO strings "YYYY-MM-DD".
    """
    if not response_dates:
        return 0.0
    return sum(
        1 for r, c in zip(response_dates, correct_effective_dates) if r == c
    ) / len(response_dates)


def leakage_detection_rate(
    predicted_risks: List[str],
    true_risks: List[str],
) -> Dict[str, float]:
    """
    LDR — how well M8 catches actual leakage attempts.
    Values are "NONE" | "LOW" | "HIGH".
    A positive = any non-NONE prediction.
    """
    tp = fp = fn = tn = 0
    for pred, true in zip(predicted_risks, true_risks):
        p_pos = pred != "NONE"
        t_pos = true != "NONE"
        if p_pos and t_pos:  tp += 1
        elif p_pos and not t_pos: fp += 1
        elif not p_pos and t_pos: fn += 1
        else: tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) else 0.0)
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def conflict_detection_rate(
    predicted_conflicts: List[bool],
    true_conflicts: List[bool],
) -> Dict[str, float]:
    """
    CDR — how well M9 catches actual jurisdiction conflicts.
    """
    tp = fp = fn = tn = 0
    for pred, true in zip(predicted_conflicts, true_conflicts):
        if pred and true:       tp += 1
        elif pred and not true: fp += 1
        elif not pred and true: fn += 1
        else:                   tn += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) else 0.0)
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def faithfulness(
    answers: List[str],
    source_contents: List[List[str]],
) -> float:
    """
    Faithfulness = fraction of answers where every factual claim appears
    (as a substring) in at least one source chunk.

    Heuristic: split answer into sentences; each sentence is 'grounded'
    if ≥1 source chunk shares ≥2 consecutive words with it.
    """
    if not answers:
        return 0.0

    def _grounded(sentence: str, sources: List[str]) -> bool:
        words = sentence.lower().split()
        if len(words) < 3:
            return True   # skip very short sentences
        bigrams = {f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)}
        for src in sources:
            src_lower = src.lower()
            if any(bg in src_lower for bg in bigrams):
                return True
        return False

    scores = []
    for answer, sources in zip(answers, source_contents):
        sentences = [s.strip() for s in answer.split(".") if s.strip()]
        if not sentences:
            scores.append(1.0)
            continue
        grounded_count = sum(1 for s in sentences if _grounded(s, sources))
        scores.append(grounded_count / len(sentences))

    return sum(scores) / len(scores)


def mean_latency(latencies: List[float]) -> Dict[str, float]:
    """
    LAT — latency statistics over a set of queries (seconds).
    """
    if not latencies:
        return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0}
    s = sorted(latencies)
    n = len(s)
    p50 = s[n // 2]
    p95 = s[int(n * 0.95)]
    return {
        "mean": sum(s) / n,
        "p50":  p50,
        "p95":  p95,
        "max":  s[-1],
    }


# ---------------------------------------------------------------------------
# Aggregated scorer
# ---------------------------------------------------------------------------

def compute_all_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute all 7 metrics from a list of evaluation result dicts.

    Each dict in `results` must have keys:
        predicted_jurisdiction  str        e.g. "IN,SG"
        true_jurisdiction       str
        detected_violations     List[str]
        true_violations         List[str]
        response_date           str        ISO date
        correct_date            str        ISO date
        predicted_leakage       str        "NONE"|"LOW"|"HIGH"
        true_leakage            str
        conflict_predicted      bool
        conflict_true           bool
        answer                  str
        source_contents         List[str]
        latency_seconds         float
    """
    return {
        "JC":  jurisdiction_correctness(
            [r["predicted_jurisdiction"] for r in results],
            [r["true_jurisdiction"]      for r in results],
        ),
        "CVR": compliance_violation_rate(
            [r["detected_violations"] for r in results],
            [r["true_violations"]     for r in results],
        ),
        "TA":  temporal_accuracy(
            [r["response_date"]  for r in results],
            [r["correct_date"]   for r in results],
        ),
        "LDR": leakage_detection_rate(
            [r["predicted_leakage"] for r in results],
            [r["true_leakage"]      for r in results],
        ),
        "CDR": conflict_detection_rate(
            [r["conflict_predicted"] for r in results],
            [r["conflict_true"]      for r in results],
        ),
        "Faithfulness": faithfulness(
            [r["answer"]          for r in results],
            [r["source_contents"] for r in results],
        ),
        "Latency": mean_latency(
            [r["latency_seconds"] for r in results],
        ),
    }
