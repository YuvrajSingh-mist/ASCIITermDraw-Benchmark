#!/usr/bin/env python3
"""
Run TermDraw-Bench L2 judging with Instructor + Pydantic.

This is useful for smaller synchronous runs where you want automatic
validation/retry behavior. Fireworks batch judging remains the scalable path.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from typing import TYPE_CHECKING

from typing import Any

try:
    from pydantic import BaseModel, ConfigDict
except ModuleNotFoundError as _PYDANTIC_ERROR:
    BaseModel = object

    def ConfigDict(**_: Any) -> dict[str, Any]:
        return {}
else:
    _PYDANTIC_ERROR = None

from lib.fireworks_api import iter_task_dirs, require_env

if TYPE_CHECKING:
    import instructor
    from openai import OpenAI


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scores: dict[str, float]
    total: float
    passed: bool
    reason: str


SYSTEM_PROMPT = (
    "You are a strict ASCII-diagram benchmark judge. "
    "Return a valid JudgeResult object. "
    "Score each checklist item as 0 or 1 in `scores`, "
    "set `total` to the sum of those checklist scores, set `passed` to true "
    "only when the diagram satisfies the task, and keep `reason` concise."
)


def normalize_l2_score(payload: JudgeResult) -> float:
    values = list(payload.scores.values())
    if values:
        return sum(values) / len(values)
    if 0.0 <= payload.total <= 1.0:
        return payload.total
    return 0.0


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


def run(
    *,
    model: str,
    tasks_dir: str,
    outputs_dir: str,
    results_path: str,
    max_retries: int,
) -> None:
    if _PYDANTIC_ERROR is not None:
        raise RuntimeError(
            "Missing Python dependency `pydantic`. "
            "Install it with `.venv/bin/python -m pip install -r requirements.txt`."
        ) from _PYDANTIC_ERROR

    try:
        import instructor
        from openai import OpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing Instructor/OpenAI dependencies. "
            "Install them with `.venv/bin/python -m pip install -r requirements.txt`."
        ) from exc

    client = instructor.from_openai(
        OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=require_env("FIREWORKS_API_KEY"),
        )
    )

    tasks = Path(tasks_dir)
    outputs = Path(outputs_dir)
    results = Path(results_path)

    existing = load_csv_rows(results)
    rows_by_task = {row["task_id"]: row for row in existing if row.get("task_id")}

    for task_dir in iter_task_dirs(tasks):
        task_id = task_dir.name
        output_file = outputs / f"{task_id}.txt"
        if not output_file.exists():
            print(f"Skipping {task_id}: missing model output")
            continue

        prompt = (task_dir / "vlm_judge_prompt.txt").read_text().replace(
            "{model_output}",
            output_file.read_text().strip(),
        )
        prompt += (
            "\n\nReturn JSON that matches the required schema exactly. "
            "Use the boolean field name `passed` instead of `pass`."
        )
        result = client.chat.completions.create(
            model=model,
            response_model=JudgeResult,
            max_retries=max_retries,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        row = rows_by_task.setdefault(task_id, {"task_id": task_id})
        l2_score = normalize_l2_score(result)
        row["L2_score"] = f"{l2_score:.4f}"
        row["L2_passed"] = str(result.passed).lower()
        row["L2_reason"] = result.reason
        row["L2_total_raw"] = str(result.total)
        if row.get("L1_total"):
            try:
                l1 = float(row["L1_total"])
                row["final_score"] = f"{(l1 + l2_score) / 2:.4f}"
            except ValueError:
                row["final_score"] = ""
        else:
            row["final_score"] = f"{l2_score:.4f}"

        judge_dir = outputs / "judge_json"
        judge_dir.mkdir(parents=True, exist_ok=True)
        (judge_dir / f"{task_id}.json").write_text(result.model_dump_json(indent=2) + "\n")
        print(f"Judged {task_id}")

    merged_rows = [rows_by_task[task_dir.name] for task_dir in iter_task_dirs(tasks)]
    save_csv_rows(results, merged_rows)
    print(f"Updated {results}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Fireworks model path")
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()
    run(
        model=args.model,
        tasks_dir=args.tasks,
        outputs_dir=args.outputs,
        results_path=args.results,
        max_retries=args.max_retries,
    )
