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
from pathlib import Path

from scripts.lib.fireworks_api import iter_task_dirs
from scripts.judge.geval_metrics import build_metric_classes, build_test_case
from scripts.judge.geval_support import StructuredJudgeBackend, build_task_artifacts
from scripts.judge.run_vlm_judge import (
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
    dry_run: bool,
) -> None:
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
        output_file = outputs / f"{task_dir.name}.txt"
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

    StructuralJudgeMetric, SemanticJudgeMetric = build_metric_classes()
    backend = StructuredJudgeBackend(
        provider=provider,
        model=model,
        max_retries=max_retries,
        artifacts_by_task_id=artifacts_by_task_id,
    )

    for task_id_value, artifacts in artifacts_by_task_id.items():
        test_case = build_test_case(task_id_value, artifacts)

        structural_metric = StructuralJudgeMetric(backend)
        semantic_metric = SemanticJudgeMetric(backend)
        structural_score = structural_metric.measure(test_case)
        semantics_score = semantic_metric.measure(test_case)

        cached = backend.judge(task_id_value)
        structural_components = structural_score_from_observations(
            artifacts.task_dir,
            cached.result.structural_observations,
        )[1]
        semantics_components = semantics_score_from_observations(
            cached.result.semantics,
        )[1]

        total_score = structural_score + semantics_score
        passed = structural_score >= 0.9999 and semantics_score >= 0.9999

        row = rows_by_task.setdefault(task_id_value, {"task_id": task_id_value})
        row["geval_provider"] = provider
        row["geval_model"] = model
        row["geval_candidate_png"] = str(artifacts.candidate_png)
        row["geval_structural_score"] = f"{structural_score:.4f}"
        row["geval_semantics_score"] = f"{semantics_score:.4f}"
        row["geval_score"] = f"{total_score:.4f}"
        row["geval_passed"] = str(passed).lower()
        row["geval_reason"] = cached.result.reason

        for key, value in structural_components.items():
            row[f"geval_structural_{key}"] = f"{value:.4f}"
        for key, value in semantics_components.items():
            if isinstance(value, float):
                row[f"geval_semantics_{key}"] = f"{value:.4f}"
            else:
                row[f"geval_semantics_{key}"] = str(value)

        output_json_dir = outputs / "judge_geval_json"
        output_json_dir.mkdir(parents=True, exist_ok=True)
        (output_json_dir / f"{task_id_value}.json").write_text(
            json.dumps(
                {
                    "provider": provider,
                    "model": model,
                    "candidate_png": str(artifacts.candidate_png),
                    "result": cached.result.model_dump(mode="json"),
                },
                indent=2,
            )
            + "\n"
        )
        print(f"Judged {task_id_value}")

    merged_rows = [
        rows_by_task[task_dir.name]
        for task_dir in iter_task_dirs(tasks)
        if task_dir.name in rows_by_task
    ]
    save_csv_rows(results, merged_rows)
    print(f"Updated {results}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["openai", "anthropic"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--task-id")
    parser.add_argument("--sample-count", type=int)
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
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
