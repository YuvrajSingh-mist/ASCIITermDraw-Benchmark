#!/usr/bin/env python3
"""
Run TermDraw-Bench multimodal judging with OpenAI or Anthropic via DeepEval BaseMetric.

The runner is intentionally thin; provider/image handling lives in
`geval_support.py`, while the custom DeepEval metrics live in
`geval_metrics.py`.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from scripts.lib.fireworks_api import iter_task_dirs, task_output_dir
from scripts.judge.geval_metrics import build_metric_classes, build_test_case
from scripts.judge.geval_support import (
    MODEL_PRICING_DEFAULTS,
    StructuredJudgeBackend,
    build_task_artifacts,
    estimate_cost_usd,
    gval_task_dir,
)
from scripts.judge.judge_schema import (
    load_csv_rows,
    save_csv_rows,
    semantics_score_from_observations,
    structural_score_from_observations,
)


def run(
    *,
    provider: str,
    model: str,
    tasks_dir: str,
    outputs_dir: str,
    results_path: str,
    max_retries: int,
    task_id: str | None,
    sample_count: int | None,
    num_judgments: int,
    judge_temperature: float | None,
    input_price_per_million: float | None,
    output_price_per_million: float | None,
    dry_run: bool,
) -> None:
    """Judge every selected task num_judgments times, aggregate mean/stdev + token usage/cost, and update the results CSV + per-task JSON."""
    tasks = Path(tasks_dir)
    outputs = Path(outputs_dir)
    results = Path(results_path)

    task_dirs = list(iter_task_dirs(tasks))
    if task_id:
        task_dirs = [task_dir for task_dir in task_dirs if task_dir.name == task_id]
    if sample_count is not None:
        task_dirs = task_dirs[:sample_count]
    if not task_dirs:
        raise RuntimeError("No task directories selected.")

    artifacts_by_task_id = {}
    for task_dir in task_dirs:
        output_file = task_output_dir(outputs, task_dir) / f"{task_dir.name}.txt"
        if not output_file.exists():
            print(f"Skipping {task_dir.name}: missing output file {output_file}")
            continue
        artifacts_by_task_id[task_dir.name] = build_task_artifacts(task_dir, outputs)

    if dry_run:
        for task_id_value, artifacts in artifacts_by_task_id.items():
            print(f"Prepared BaseMetric judge case for {task_id_value} -> {artifacts.candidate_png}")
        return

    existing = load_csv_rows(results)
    rows_by_task = {row["task_id"]: row for row in existing if row.get("task_id")}

    if input_price_per_million is None and output_price_per_million is None:
        input_price_per_million, output_price_per_million = MODEL_PRICING_DEFAULTS.get(
            (provider.lower(), model.lower()), (None, None)
        )

    StructuralJudgeMetric, SemanticJudgeMetric = build_metric_classes()
    backend = StructuredJudgeBackend(
        provider=provider,
        model=model,
        max_retries=max_retries,
        artifacts_by_task_id=artifacts_by_task_id,
        outputs_dir=outputs,
        temperature=judge_temperature,
    )

    for task_id_value, artifacts in artifacts_by_task_id.items():
        test_case = build_test_case(task_id_value, artifacts)

        structural_scores: list[float] = []
        semantics_scores: list[float] = []
        structural_components_by_key: dict[str, list[float]] = {}
        semantics_components_by_key: dict[str, list[float]] = {}
        rounds_payload: list[dict[str, object]] = []
        reasons: list[str] = []
        total_input_tokens = 0
        total_output_tokens = 0

        for round_index in range(num_judgments):
            structural_metric = StructuralJudgeMetric(backend, round_index=round_index)
            semantic_metric = SemanticJudgeMetric(backend, round_index=round_index)
            structural_score = structural_metric.measure(test_case)
            semantics_score = semantic_metric.measure(test_case)

            cached = backend.judge(task_id_value, round_index)
            structural_components = structural_score_from_observations(
                artifacts.task_dir,
                cached.result.structural_observations,
            )[1]
            semantics_components = semantics_score_from_observations(
                cached.result.semantics,
            )[1]

            structural_scores.append(structural_score)
            semantics_scores.append(semantics_score)
            reasons.append(cached.result.reason)
            total_input_tokens += cached.usage.input_tokens
            total_output_tokens += cached.usage.output_tokens
            for key, value in structural_components.items():
                structural_components_by_key.setdefault(key, []).append(float(value))
            for key, value in semantics_components.items():
                semantics_components_by_key.setdefault(key, []).append(float(value))

            rounds_payload.append(
                {
                    "round": round_index,
                    "structural_score": structural_score,
                    "semantics_score": semantics_score,
                    "reason": cached.result.reason,
                    "input_tokens": cached.usage.input_tokens,
                    "output_tokens": cached.usage.output_tokens,
                    "result": cached.result.model_dump(mode="json"),
                }
            )
            print(f"Judged {task_id_value} (round {round_index + 1}/{num_judgments})")

        mean_structural = statistics.mean(structural_scores)
        mean_semantics = statistics.mean(semantics_scores)
        stdev_structural = statistics.pstdev(structural_scores)
        stdev_semantics = statistics.pstdev(semantics_scores)
        structural_components = {key: statistics.mean(values) for key, values in structural_components_by_key.items()}
        semantics_components = {key: statistics.mean(values) for key, values in semantics_components_by_key.items()}

        # Computed directly from the paired per-round sums rather than via
        # sqrt(stdev_structural**2 + stdev_semantics**2): the two scores come
        # from the same judge call each round, so they aren't independent,
        # and this way the true round-to-round covariance (whatever it is)
        # is captured automatically instead of assumed away.
        total_scores = [s + m for s, m in zip(structural_scores, semantics_scores)]
        stdev_total = statistics.pstdev(total_scores)

        total_score = mean_structural + mean_semantics
        passed = mean_structural >= 0.9999 and mean_semantics >= 0.9999
        cost_usd = estimate_cost_usd(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            input_price_per_million=input_price_per_million,
            output_price_per_million=output_price_per_million,
        )

        row = rows_by_task.setdefault(task_id_value, {"task_id": task_id_value})
        row["geval_provider"] = provider
        row["geval_model"] = model
        row["geval_candidate_png"] = str(artifacts.candidate_png)
        row["geval_num_judgments"] = str(num_judgments)
        row["geval_structural_score"] = f"{mean_structural:.4f}"
        row["geval_semantics_score"] = f"{mean_semantics:.4f}"
        row["geval_structural_stdev"] = f"{stdev_structural:.4f}"
        row["geval_semantics_stdev"] = f"{stdev_semantics:.4f}"
        row["geval_score"] = f"{total_score:.4f}"
        row["geval_score_stdev"] = f"{stdev_total:.4f}"
        row["geval_passed"] = str(passed).lower()
        row["geval_reason"] = reasons[-1]
        row["geval_input_tokens"] = str(total_input_tokens)
        row["geval_output_tokens"] = str(total_output_tokens)
        row["geval_total_tokens"] = str(total_input_tokens + total_output_tokens)
        row["geval_cost_usd"] = f"{cost_usd:.6f}" if cost_usd is not None else ""

        for key, value in structural_components.items():
            row[f"geval_structural_{key}"] = f"{value:.4f}"
        for key, value in semantics_components.items():
            row[f"geval_semantics_{key}"] = f"{value:.4f}"

        gval_dir = gval_task_dir(outputs, artifacts.task_dir)
        gval_dir.mkdir(parents=True, exist_ok=True)
        (gval_dir / "result.json").write_text(
            json.dumps(
                {
                    "provider": provider,
                    "model": model,
                    "candidate_png": str(artifacts.candidate_png),
                    "num_judgments": num_judgments,
                    "mean_structural_score": mean_structural,
                    "mean_semantics_score": mean_semantics,
                    "stdev_structural_score": stdev_structural,
                    "stdev_semantics_score": stdev_semantics,
                    "mean_total_score": total_score,
                    "stdev_total_score": stdev_total,
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "cost_usd": cost_usd,
                    "rounds": rounds_payload,
                },
                indent=2,
            )
            + "\n"
        )
        cost_note = f", cost=${cost_usd:.4f}" if cost_usd is not None else ""
        print(
            f"Aggregated {task_id_value}: structural={mean_structural:.4f}±{stdev_structural:.4f}, "
            f"semantics={mean_semantics:.4f}±{stdev_semantics:.4f}, "
            f"tokens={total_input_tokens}in/{total_output_tokens}out{cost_note}"
        )

    merged_rows = [
        rows_by_task[task_dir.name]
        for task_dir in iter_task_dirs(tasks)
        if task_dir.name in rows_by_task
    ]
    save_csv_rows(results, merged_rows)
    print(f"Updated {results}")


def main() -> None:
    """CLI entrypoint for `judge-geval`: parse args and run the DeepEval judge."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["openai", "anthropic"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--task-id")
    parser.add_argument("--sample-count", type=int)
    parser.add_argument(
        "--num-judgments",
        type=int,
        default=5,
        help="Repeat the judge call this many times per task and report mean/stdev, to average out judge-model noise. Default 10, matching common LLM-as-judge reliability practice.",
    )
    parser.add_argument(
        "--judge-temperature",
        type=float,
        help="Override the judge model's sampling temperature (otherwise left at the provider's default). Raise this to widen the spread across --num-judgments rounds.",
    )
    parser.add_argument(
        "--input-price-per-million",
        type=float,
        help="USD price per 1M input tokens for the judge model, to compute geval_cost_usd. Known models (gpt-5.4, claude-sonnet-5) have built-in defaults; this flag overrides.",
    )
    parser.add_argument(
        "--output-price-per-million",
        type=float,
        help="USD price per 1M output tokens for the judge model, to compute geval_cost_usd. Known models (gpt-5.4, claude-sonnet-5) have built-in defaults; this flag overrides.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(
        provider=args.provider,
        model=args.model,
        tasks_dir=args.tasks,
        outputs_dir=args.outputs,
        results_path=args.results,
        max_retries=args.max_retries,
        task_id=args.task_id,
        sample_count=args.sample_count,
        num_judgments=args.num_judgments,
        judge_temperature=args.judge_temperature,
        input_price_per_million=args.input_price_per_million,
        output_price_per_million=args.output_price_per_million,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
