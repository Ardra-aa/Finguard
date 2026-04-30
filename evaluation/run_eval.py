"""
M10 — Evaluation Harness
Runs all 4 baseline systems against all 6 test sets and
produces a JSON report + formatted comparison table.

Usage:
    python -m evaluation.run_eval                          # all baselines, all test sets
    python -m evaluation.run_eval --baseline B4 --set E   # specific run
"""

from __future__ import annotations
import argparse
import json
import time
from typing import Any, Dict, List

from .metrics import compute_all_metrics
from .baselines import ALL_BASELINES, VanillaRAG, RBACFilteredRAG, TemporalFilteredRAG, FinGuardRAG
from .test_sets.test_cases import ALL_TEST_SETS


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _run_baseline_on_set(baseline, test_cases: List[dict]) -> List[Dict[str, Any]]:
    """Run one baseline over one test set, return eval-ready result dicts."""
    results = []
    for case in test_cases:
        t0 = time.time()
        output = baseline.run(
            query        = case["query"],
            user_context = case["user_context"],
        )
        latency = time.time() - t0

        # Merge pipeline output with ground-truth labels
        result = {
            # Ground truth
            "case_id":              case["case_id"],
            "set_id":               case["set_id"],
            "true_jurisdiction":    case["true_jurisdiction"],
            "true_violations":      case["true_violations"],
            "correct_date":         case["correct_date"],
            "true_leakage":         case["true_leakage"],
            "conflict_true":        case["conflict_true"],

            # Predictions from pipeline
            "predicted_jurisdiction": output.get("predicted_jurisdiction", "IN"),
            "detected_violations":    output.get("violations", []),
            "response_date":          output.get("response_date", case["correct_date"]),
            "predicted_leakage":      output.get("leakage_risk", "NONE"),
            "conflict_predicted":     output.get("conflict_detected", False),
            "answer":                 output.get("answer", ""),
            "source_contents":        [s.content if hasattr(s, "content") else str(s)
                                       for s in output.get("sources", [])],
            "latency_seconds":        latency,
        }
        results.append(result)
    return results


def run_evaluation(
    baseline_names: List[str] | None = None,
    test_set_ids:   List[str] | None = None,
    output_path:    str = "evaluation_report.json",
) -> Dict[str, Any]:
    """
    Run evaluation. Returns the full report dict.

    Parameters
    ----------
    baseline_names : list of baseline name strings e.g. ["B1_VanillaRAG", "B4_FinGuardRAG"]
                     None = run all 4
    test_set_ids   : list of set IDs e.g. ["A", "E"]
                     None = run all 6
    output_path    : path to write JSON report
    """
    baselines = ALL_BASELINES
    if baseline_names:
        baselines = [b for b in ALL_BASELINES if b.name in baseline_names]

    sets_to_run = {k: v for k, v in ALL_TEST_SETS.items()
                   if test_set_ids is None or k in test_set_ids}

    report: Dict[str, Any] = {"baselines": {}}

    for baseline in baselines:
        print(f"\n{'='*60}")
        print(f"  Running baseline: {baseline.name}")
        print(f"{'='*60}")

        baseline_report = {"sets": {}, "aggregate": {}}
        all_results: List[Dict[str, Any]] = []

        for set_id, test_cases in sets_to_run.items():
            results = _run_baseline_on_set(baseline, test_cases)
            set_metrics = compute_all_metrics(results)
            baseline_report["sets"][set_id] = {
                "metrics": set_metrics,
                "n_cases": len(results),
            }
            all_results.extend(results)
            print(f"  Set {set_id}: {len(results)} cases — "
                  f"JC={set_metrics['JC']:.2f}  "
                  f"LDR_F1={set_metrics['LDR']['f1']:.2f}  "
                  f"CDR_F1={set_metrics['CDR']['f1']:.2f}  "
                  f"Faith={set_metrics['Faithfulness']:.2f}  "
                  f"Lat_p95={set_metrics['Latency']['p95']:.3f}s")

        aggregate = compute_all_metrics(all_results)
        baseline_report["aggregate"] = aggregate
        report["baselines"][baseline.name] = baseline_report

    # Save JSON report
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {output_path}")

    # Print comparison table
    _print_comparison_table(report)

    return report


def _print_comparison_table(report: dict) -> None:
    """Print a formatted side-by-side comparison of all baselines."""
    baselines = list(report["baselines"].keys())
    metrics   = ["JC", "TA", "Faithfulness"]
    sub_metrics = [("CVR", "f1"), ("LDR", "f1"), ("CDR", "f1"),
                   ("Latency", "p95")]

    header = f"{'Metric':<22}" + "".join(f"{b:<22}" for b in baselines)
    print("\n" + "=" * (22 + 22 * len(baselines)))
    print(header)
    print("=" * (22 + 22 * len(baselines)))

    def _val(baseline_name, key, sub=None):
        agg = report["baselines"][baseline_name]["aggregate"]
        v = agg.get(key, 0)
        if sub:
            v = v.get(sub, 0) if isinstance(v, dict) else 0
        return f"{v:.3f}"

    for m in metrics:
        row = f"{m:<22}" + "".join(f"{_val(b, m):<22}" for b in baselines)
        print(row)

    for m, sub in sub_metrics:
        label = f"{m}.{sub}"
        row = f"{label:<22}" + "".join(f"{_val(b, m, sub):<22}" for b in baselines)
        print(row)

    print("=" * (22 + 22 * len(baselines)))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinGuard-RAG Evaluation Harness")
    parser.add_argument("--baseline", nargs="*", help="Baseline name(s) to run")
    parser.add_argument("--set",      nargs="*", help="Test set ID(s) to run (A-F)")
    parser.add_argument("--output",   default="evaluation_report.json",
                        help="Output JSON path")
    args = parser.parse_args()

    run_evaluation(
        baseline_names = args.baseline,
        test_set_ids   = args.set,
        output_path    = args.output,
    )
