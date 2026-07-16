#!/usr/bin/env python3
"""
Run multimodal GEval judging for TermDraw-Bench.

This adapts the retry/batching structure from smolcluster's
evaluate_summarization.py for benchmark image judging.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lib.fireworks_api import iter_task_dirs


ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def backoff_seconds(attempt: int) -> float:
    return min(2.0 ** (attempt - 1), 20.0)


def render_ascii_to_png(ascii_text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".ascii", delete=False) as tmp:
        tmp.write(ascii_text.rstrip("\n") + "\n")
        temp_ascii_path = Path(tmp.name)
    try:
        subprocess.run(
            [
                "node",
                str(ROOT / "scripts" / "rendered" / "render_ascii.mjs"),
                str(temp_ascii_path),
                str(output_path),
            ],
            check=True,
            timeout=60,
        )
    finally:
        temp_ascii_path.unlink(missing_ok=True)


def resolve_candidate_png(task_dir: Path, outputs_dir: Path) -> Path:
    rendered_dir = outputs_dir / "judge_geval_rendered"
    candidate_png = rendered_dir / f"{task_dir.name}.png"
    if candidate_png.exists():
        return candidate_png

    output_file = outputs_dir / f"{task_dir.name}.txt"
    output_text = output_file.read_text().strip()
    render_ascii_to_png(output_text, candidate_png)
    return candidate_png


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def save_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def chunked(items: list[Any], size: int) -> list[list[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def natural_task_sort_key(task_id: str) -> list[Any]:
    parts: list[Any] = []
    for piece in task_id.split("."):
        parts.append(int(piece) if piece.isdigit() else piece)
    return parts


@dataclass
class MetricSpec:
    name: str
    steps: list[str]


STRUCTURAL_METRIC = MetricSpec(
    name="Structural Accuracy",
    steps=[
        "Use the task-specific judge prompt, prompt text, assertions JSON, and reference image together as the target specification.",
        "Judge structural accuracy only by the structural rubric defined in the task-specific judge prompt.",
        "For non-editing tasks, evaluate whether the candidate gets the required labels, entity count, and required edges correct.",
        "When required edge labels are part of the assertions for the task, include them in structural judgment.",
        "For editing tasks, also evaluate preserved elements according to the task-specific judge prompt and assertions JSON.",
        "A score of 1.0 means the candidate structurally matches the benchmark target under that structural rubric; 0.0 means it fails most required structure.",
    ],
)

SEMANTIC_METRIC = MetricSpec(
    name="Semantic and Layout Accuracy",
    steps=[
        "Use the task-specific judge prompt, prompt text, and reference image together as the target specification.",
        "Judge semantic and layout accuracy only by the semantics rubric defined in the task-specific judge prompt.",
        "This includes: connections being correct; text inside nodes being correct; text being visually centered inside nodes; layout matching the prompt strictly; visible labels being spelled correctly; and arrows being cleanly aligned, with arrow labels sitting a little above the arrow rather than inside it.",
        "For editing tasks, penalize any unrequested edits and reward preserving the original structure outside the requested changes exactly as described in the task-specific judge prompt.",
        "A score of 1.0 means the candidate semantically and visually matches the benchmark target under that semantics rubric; 0.0 means it clearly violates the prompt or visual constraints.",
    ],
)


def build_metrics(model: Any) -> list[Any]:
    from deepeval.metrics import GEval
    from deepeval.test_case import SingleTurnParams

    return [
        GEval(
            name=spec.name,
            model=model,
            evaluation_params=[
                SingleTurnParams.INPUT,
                SingleTurnParams.ACTUAL_OUTPUT,
                SingleTurnParams.EXPECTED_OUTPUT,
            ],
            evaluation_steps=spec.steps,
            threshold=0.5,
            async_mode=True,
            strict_mode=False,
            verbose_mode=False,
        )
        for spec in [STRUCTURAL_METRIC, SEMANTIC_METRIC]
    ]


def build_model(provider: str, model_name: str) -> Any:
    if provider == "openai":
        from deepeval.models import GPTModel

        return GPTModel(
            model=model_name,
            api_key=require_env("OPENAI_API_KEY"),
            temperature=0,
            generation_kwargs={"max_completion_tokens": 2048},
        )
    if provider == "anthropic":
        from deepeval.models import AnthropicModel

        return AnthropicModel(
            model=model_name,
            api_key=require_env("ANTHROPIC_API_KEY"),
            generation_kwargs={"max_tokens": 2048},
        )
    raise ValueError(f"Unsupported provider: {provider}")


def build_test_case(task_dir: Path, outputs_dir: Path) -> tuple[Any, Path]:
    from deepeval.test_case import LLMTestCase, MLLMImage

    candidate_png = resolve_candidate_png(task_dir, outputs_dir)
    output_text = (outputs_dir / f"{task_dir.name}.txt").read_text().strip()

    prompt_text = (task_dir / "prompt.txt").read_text().strip()
    assertions = json.loads((task_dir / "assertions.json").read_text())
    task_specific_judge_prompt = (
        (task_dir / "vlm_judge_prompt.txt")
        .read_text()
        .replace(
            "{model_output}",
            "Candidate generated image is provided separately in ACTUAL_OUTPUT. "
            "Use that candidate image as the model output for judging.",
        )
        .strip()
    )
    reference_image = MLLMImage(url=str(task_dir / "reference.png"))
    candidate_image = MLLMImage(url=str(candidate_png))

    source_text = ""
    if (task_dir / "source.png").exists():
        source_image = MLLMImage(url=str(task_dir / "source.png"))
        source_text = (
            "Editing-task image order:\n"
            "1. Original source image before edits:\n"
            f"{source_image}\n\n"
            "2. Target reference image after the requested edits:\n"
            f"{reference_image}\n\n"
            "3. Candidate generated image is provided separately in ACTUAL_OUTPUT.\n\n"
        )

    test_case = LLMTestCase(
        name=task_dir.name,
        input=(
            "Benchmark task materials:\n"
            f"Task ID: {task_dir.name}\n\n"
            f"Prompt:\n{prompt_text}\n\n"
            f"Assertions JSON:\n{json.dumps(assertions, indent=2)}\n\n"
            "Task-specific VLM judge prompt:\n"
            f"{task_specific_judge_prompt}\n\n"
            "Candidate ASCII text for reference:\n"
            f"{output_text}\n\n"
            f"{source_text}"
            "Target reference image:\n"
            f"{reference_image}\n\n"
            "Evaluate the candidate image against the task-specific judge prompt, prompt, assertions, and target reference image."
        ),
        actual_output=f"Candidate generated image:\n{candidate_image}",
        expected_output=f"Target reference image:\n{reference_image}",
    )
    return test_case, candidate_png


def render_candidate_only(task_dir: Path, outputs_dir: Path) -> Path:
    return resolve_candidate_png(task_dir, outputs_dir)


def parse_metric_data(metrics_data: list[Any] | None) -> dict[str, dict[str, Any]]:
    parsed: dict[str, dict[str, Any]] = {}
    for metric in metrics_data or []:
        parsed[metric.name] = {
            "score": metric.score,
            "reason": metric.reason,
            "success": metric.success,
            "error": metric.error,
            "evaluation_model": metric.evaluation_model,
            "evaluation_cost": metric.evaluation_cost,
            "input_tokens": metric.input_tokens,
            "output_tokens": metric.output_tokens,
        }
    return parsed


def selected_task_dirs(tasks_dir: Path, task_id: str | None, sample_count: int | None) -> list[Path]:
    task_dirs = list(iter_task_dirs(tasks_dir))
    if task_id:
        task_dirs = [task_dir for task_dir in task_dirs if task_dir.name == task_id]
    if sample_count is not None:
        task_dirs = task_dirs[:sample_count]
    return task_dirs


def run(
    *,
    provider: str,
    model_name: str,
    tasks_dir: str,
    outputs_dir: str,
    results_path: str,
    batch_size: int,
    max_concurrent: int,
    throttle_seconds: float,
    max_retries: int,
    task_id: str | None,
    sample_count: int | None,
    dry_run: bool,
) -> None:
    load_dotenv(ROOT / ".env")

    tasks = Path(tasks_dir)
    outputs = Path(outputs_dir)
    results = Path(results_path)

    task_dirs = selected_task_dirs(tasks, task_id, sample_count)
    if not task_dirs:
        raise RuntimeError("No task directories selected.")

    existing = load_csv_rows(results)
    rows_by_task = {row["task_id"]: row for row in existing if row.get("task_id")}

    if dry_run:
        for task_dir in task_dirs:
            output_file = outputs / f"{task_dir.name}.txt"
            if not output_file.exists():
                print(f"Skipping {task_dir.name}: missing output file {output_file}")
                continue
            candidate_png = render_candidate_only(task_dir, outputs)
            print(f"Prepared GEval test case for {task_dir.name} -> {candidate_png}")
        return

    from deepeval import evaluate as deepeval_evaluate
    from deepeval.evaluate.configs import AsyncConfig, DisplayConfig

    built_cases: list[tuple[Path, Any, Path]] = []
    for task_dir in task_dirs:
        output_file = outputs / f"{task_dir.name}.txt"
        if not output_file.exists():
            print(f"Skipping {task_dir.name}: missing output file {output_file}")
            continue
        test_case, candidate_png = build_test_case(task_dir, outputs)
        built_cases.append((task_dir, test_case, candidate_png))

    judge_model = build_model(provider, model_name)
    async_config = AsyncConfig(
        run_async=max_concurrent > 1,
        max_concurrent=max_concurrent,
        throttle_value=throttle_seconds,
    )
    display_config = DisplayConfig(show_indicator=False, print_results=False)

    total_cases = 0
    for batch in chunked(built_cases, batch_size):
        test_cases = [test_case for _, test_case, _ in batch]
        for attempt in range(1, max_retries + 1):
            try:
                result = deepeval_evaluate(
                    test_cases=test_cases,
                    metrics=build_metrics(judge_model),
                    async_config=async_config,
                    display_config=display_config,
                )
                for (task_dir, _, _), test_result in zip(batch, result.test_results):
                    metric_map = parse_metric_data(test_result.metrics_data)
                    structural = metric_map.get("Structural Accuracy", {})
                    semantic = metric_map.get("Semantic and Layout Accuracy", {})
                    scores = [
                        score
                        for score in [structural.get("score"), semantic.get("score")]
                        if score is not None
                    ]
                    mean_score = sum(scores) / len(scores) if scores else 0.0

                    row = rows_by_task.setdefault(task_dir.name, {"task_id": task_dir.name})
                    row["geval_provider"] = provider
                    row["geval_model"] = model_name
                    row["geval_structural_score"] = f"{float(structural.get('score') or 0.0):.4f}"
                    row["geval_structural_reason"] = structural.get("reason") or ""
                    row["geval_semantic_score"] = f"{float(semantic.get('score') or 0.0):.4f}"
                    row["geval_semantic_reason"] = semantic.get("reason") or ""
                    row["geval_score"] = f"{mean_score:.4f}"
                    row["geval_passed"] = str(bool(structural.get("success")) and bool(semantic.get("success"))).lower()

                    output_json_dir = outputs / "judge_geval_json"
                    output_json_dir.mkdir(parents=True, exist_ok=True)
                    (output_json_dir / f"{task_dir.name}.json").write_text(
                        json.dumps(
                            {
                                "task_id": task_dir.name,
                                "provider": provider,
                                "model": model_name,
                                "metrics": metric_map,
                            },
                            indent=2,
                        )
                        + "\n"
                    )
                    print(f"GEval judged {task_dir.name}")
                    total_cases += 1
                break
            except Exception as exc:  # noqa: BLE001
                if attempt >= max_retries:
                    raise
                sleep_seconds = backoff_seconds(attempt)
                print(
                    f"Retrying GEval batch after failure ({attempt}/{max_retries}): {exc}. "
                    f"Sleeping {sleep_seconds:.1f}s."
                )
                time.sleep(sleep_seconds)

    merged_rows = [
        rows_by_task[key]
        for key in sorted(rows_by_task.keys(), key=natural_task_sort_key)
    ]
    save_csv_rows(results, merged_rows)
    print(f"Updated {results} with {total_cases} GEval judgments")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["openai", "anthropic"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--max-concurrent", type=int, default=5)
    parser.add_argument("--throttle-seconds", type=float, default=0.05)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--task-id")
    parser.add_argument("--sample-count", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(
        provider=args.provider,
        model_name=args.model,
        tasks_dir=args.tasks,
        outputs_dir=args.outputs,
        results_path=args.results,
        batch_size=args.batch_size,
        max_concurrent=args.max_concurrent,
        throttle_seconds=args.throttle_seconds,
        max_retries=args.max_retries,
        task_id=args.task_id,
        sample_count=args.sample_count,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
