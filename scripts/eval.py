#!/usr/bin/env python3
"""
TermDraw-Bench L1 (deterministic structural) evaluation harness (the `eval`
console script) — scores generated ASCII outputs against each task's
assertions.json, independent of the judge-geval semantic judge.

Usage:
    uv run eval --outputs outputs/model_name/ --tasks tasks/ --results results.csv

Expects outputs/model_name/ to mirror the tasks/ layout, containing files at
<category>/<difficulty>/<task_id>/{task_id}.txt
(e.g. box-layout-basics/easy/1.1/1.1.txt)

For C3 tasks, model output is still plain text (ASCII diagram).
The image was the input; the output is always text.
"""
import csv
import argparse
from pathlib import Path
from scripts.lib.checker import score, load_assertions
from scripts.lib.fireworks_api import iter_task_dirs, task_output_dir

def run_eval(outputs_dir: str, tasks_dir: str, results_path: str):
    """Score every task's generated output against its assertions.json and write an L1 results CSV."""
    outputs = Path(outputs_dir)
    tasks   = Path(tasks_dir)
    rows    = []

    for task_dir in iter_task_dirs(tasks):
        task_id = task_dir.name
        output_file = task_output_dir(outputs, task_dir) / f"{task_id}.txt"
        assertions_file = task_dir / "assertions.json"

        if not output_file.exists():
            print(f"MISSING output: {task_id}")
            continue
        if not assertions_file.exists():
            print(f"MISSING assertions: {task_id}")
            continue

        output_text = output_file.read_text()
        assertions  = load_assertions(str(assertions_file))
        l1_result   = score(output_text, assertions)

        row = {"task_id": task_id, **l1_result}
        rows.append(row)
        print(f"{task_id}: L1={l1_result['L1_total']:.3f}")

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(results_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nResults written to {results_path}")
        avg = sum(r["L1_total"] for r in rows) / len(rows)
        print(f"Mean L1: {avg:.3f} across {len(rows)} tasks")

def main() -> None:
    """CLI entrypoint for `eval`: parse args and run L1 scoring."""
    p = argparse.ArgumentParser()
    p.add_argument("--outputs", required=True)
    p.add_argument("--tasks",   default="tasks")
    p.add_argument("--results", default="results.csv")
    args = p.parse_args()
    run_eval(args.outputs, args.tasks, args.results)


if __name__ == "__main__":
    main()
