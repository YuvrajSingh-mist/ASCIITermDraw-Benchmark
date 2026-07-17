#!/usr/bin/env python3
"""Aggregate gval/result.json round-level scores into metrics.json (the `compute-metrics` console script).

For structural and semantics separately: flattens every judge round across
all tasks into one sample list and takes its population mean/stdev
(statistics.mean/statistics.pstdev). Because every task has the same
number of judge rounds, this flat computation is mathematically identical
to combining each task's own (mean, stdev) via the law of total variance
(between-task variance + mean within-task variance) -- it just lets the
standard library do that combination instead of a manual formula.

The two per-axis results are then combined into one final score by
averaging the means and combining the stdevs with the standard
Var((X+Y)/2) = (Var(X) + Var(Y) + 2*Cov(X,Y)) / 4 identity, using
statistics.covariance (converted from sample to population covariance)
for the Cov(X,Y) term rather than assuming independence.

final_score also gets a 95% confidence interval on the mean. This uses
the 80 *tasks* as the independent sampling unit (not the 400 judge
rounds): each task's own mean_structural_score/mean_semantics_score is
already an average over its 5 rounds, and those 5 rounds are repeated
measurements of the same task, not independent draws from the task
population, so treating them as 400 independent samples would understate
the standard error. CI95 = mean +/- 1.96 * (sample_stdev / sqrt(80)).
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def population_covariance(x: list[float], y: list[float]) -> float:
    """Population covariance between paired samples x and y, derived from statistics.covariance (sample covariance)."""
    n = len(x)
    sample_cov = statistics.covariance(x, y)
    return sample_cov * (n - 1) / n


def load_round_scores(outputs_dir: Path) -> tuple[list[float], list[float]]:
    """Flatten every judge round's structural_score/semantics_score across every task's gval/result.json under outputs_dir."""
    structural: list[float] = []
    semantics: list[float] = []
    result_paths = sorted(outputs_dir.rglob("gval/result.json"))
    if not result_paths:
        raise RuntimeError(f"No gval/result.json files found under {outputs_dir}")
    for result_path in result_paths:
        payload = json.loads(result_path.read_text())
        for round_entry in payload["rounds"]:
            structural.append(round_entry["structural_score"])
            semantics.append(round_entry["semantics_score"])
    return structural, semantics


def load_per_task_final_scores(outputs_dir: Path) -> list[float]:
    """Per-task final score: the average of that task's own mean_structural_score and mean_semantics_score (each already averaged over its 5 judge rounds)."""
    scores: list[float] = []
    for result_path in sorted(outputs_dir.rglob("gval/result.json")):
        payload = json.loads(result_path.read_text())
        scores.append(
            (payload["mean_structural_score"] + payload["mean_semantics_score"]) / 2
        )
    return scores


def confidence_interval_95(task_scores: list[float]) -> dict:
    """95% CI on the population mean, treating each task as an independent sample (not the 5 judge rounds within it)."""
    n = len(task_scores)
    mean = statistics.mean(task_scores)
    sample_stdev = statistics.stdev(task_scores)
    standard_error = sample_stdev / (n**0.5)
    margin = 1.96 * standard_error
    return {
        "mean": round(mean, 4),
        "margin": round(margin, 4),
        "low": round(mean - margin, 4),
        "high": round(mean + margin, 4),
        "n_tasks": n,
        "sample_stdev": round(sample_stdev, 4),
    }


def compute_metrics(outputs_dir: Path, model_name: str) -> dict:
    structural, semantics = load_round_scores(outputs_dir)
    num_tasks = len(structural) // 5 if len(structural) % 5 == 0 else None

    mean_structural = statistics.mean(structural)
    stdev_structural = statistics.pstdev(structural)
    mean_semantics = statistics.mean(semantics)
    stdev_semantics = statistics.pstdev(semantics)

    cov_structural_semantics = population_covariance(structural, semantics)

    final_mean = (mean_structural + mean_semantics) / 2
    final_var = (
        stdev_structural**2 + stdev_semantics**2 + 2 * cov_structural_semantics
    ) / 4
    final_stdev = final_var**0.5

    per_task_scores = load_per_task_final_scores(outputs_dir)
    final_ci95 = confidence_interval_95(per_task_scores)

    return {
        "model": model_name,
        "num_tasks": num_tasks,
        "num_judge_rounds_per_task": 5,
        "structural": {
            "mean": round(mean_structural, 4),
            "stdev": round(stdev_structural, 4),
        },
        "semantics": {
            "mean": round(mean_semantics, 4),
            "stdev": round(stdev_semantics, 4),
        },
        "covariance_structural_semantics": round(cov_structural_semantics, 6),
        "final_score": {
            "mean": round(final_mean, 4),
            "stdev": round(final_stdev, 4),
            "max_possible": 1.0,
            "ci95": final_ci95,
        },
        "notes": (
            "structural.stdev and semantics.stdev are each the population stdev "
            "(statistics.pstdev) over every judge round across all tasks (task means "
            "and within-task round variance combined via the flat computation, which "
            "is mathematically identical to law-of-total-variance since every task has "
            "the same number of rounds). final_score is the average of structural.mean "
            "and semantics.mean; final_score.stdev is derived from "
            "Var((S+M)/2) = (Var(S) + Var(M) + 2*Cov(S,M)) / 4 using the population "
            "covariance between structural and semantics scores (statistics.covariance, "
            "converted from sample to population covariance) rather than assuming "
            "independence. final_score.ci95 is a 95% confidence interval on the mean "
            "using the 80 tasks as the independent sampling unit (sample_stdev over "
            "each task's own final score / sqrt(80), not the 400 judge rounds, since "
            "rounds are repeated measurements of the same task rather than independent "
            "samples)."
        ),
    }


def main() -> None:
    """CLI entrypoint for `compute-metrics`: parse args and write metrics.json."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outputs",
        required=True,
        help="Model outputs directory, e.g. outputs/qwen3p7-plus",
    )
    parser.add_argument(
        "--model", required=True, help="Model name to record in metrics.json"
    )
    parser.add_argument(
        "--out", help="Where to write metrics.json (defaults to <outputs>/metrics.json)"
    )
    args = parser.parse_args()

    outputs_dir = Path(args.outputs)
    metrics = compute_metrics(outputs_dir, args.model)

    # Pull generation cost/token totals from manifest.json (the source of truth
    # written by run-model), falling back to an existing metrics.json if the
    # manifest predates cost tracking.
    manifest_path = outputs_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if "total_cost_usd" in manifest:
            metrics["generation_cost_usd"] = manifest["total_cost_usd"]
        if "total_input_tokens" in manifest:
            metrics["generation_input_tokens"] = manifest["total_input_tokens"]
        if "total_output_tokens" in manifest:
            metrics["generation_output_tokens"] = manifest["total_output_tokens"]

    out_path = Path(args.out) if args.out else outputs_dir / "metrics.json"
    if out_path.exists() and "generation_cost_usd" not in metrics:
        existing = json.loads(out_path.read_text())
        for key in (
            "generation_cost_usd",
            "generation_input_tokens",
            "generation_output_tokens",
        ):
            if key in existing:
                metrics[key] = existing[key]

    out_path.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"Wrote {out_path}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
