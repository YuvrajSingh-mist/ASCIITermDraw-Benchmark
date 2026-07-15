#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from textwrap import dedent


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.benchmark.prompts import (  # noqa: E402
    build_judge_prompt,
    finalize_task_prompt,
    normalize_assertions,
)
from scripts.benchmark.tasks import (  # noqa: E402
    TASK_CATEGORY_DIRS,
    load_tasks,
    task_difficulty_bucket,
)


def audit(tasks_root: Path, data_dir: Path) -> int:
    tasks = load_tasks(data_dir)
    expected_dirs: set[Path] = set()
    issues: list[str] = []

    for task_id, data in tasks.items():
        category = task_id.split(".", 1)[0]
        task_dir = (
            tasks_root
            / TASK_CATEGORY_DIRS.get(category, category)
            / task_difficulty_bucket(task_id)
            / task_id
        )
        expected_dirs.add(task_dir)
        assertions = normalize_assertions(task_id, data["assertions"])
        expected_prompt = finalize_task_prompt(task_id, data["prompt"], assertions)
        expected_reference = dedent(data["reference"]).strip("\n")
        expected_judge = build_judge_prompt(
            task_id,
            expected_prompt,
            assertions,
            data.get("source"),
        )
        if not task_dir.exists():
            issues.append(f"missing task directory: {task_dir}")
            continue

        prompt_path = task_dir / "prompt.txt"
        if not prompt_path.exists() or prompt_path.read_text().strip() != expected_prompt:
            issues.append(f"{task_id}: prompt.txt mismatch")

        assertions_path = task_dir / "assertions.json"
        if not assertions_path.exists():
            issues.append(f"{task_id}: missing assertions.json")
        else:
            actual_assertions = json.loads(assertions_path.read_text())
            if actual_assertions != assertions:
                issues.append(f"{task_id}: assertions.json mismatch")

        reference_ascii_path = task_dir / "reference.ascii"
        if (
            not reference_ascii_path.exists()
            or reference_ascii_path.read_text().strip("\n") != expected_reference
        ):
            issues.append(f"{task_id}: reference.ascii mismatch")

        judge_path = task_dir / "vlm_judge_prompt.txt"
        if not judge_path.exists() or judge_path.read_text().strip() != expected_judge:
            issues.append(f"{task_id}: vlm_judge_prompt.txt mismatch")

        reference_png = task_dir / "reference.png"
        if not reference_png.exists() or reference_png.stat().st_size == 0:
            issues.append(f"{task_id}: missing or empty reference.png")

        if data.get("source") is not None:
            source_ascii = dedent(data["source"]).strip("\n")
            source_ascii_path = task_dir / "source.ascii"
            if (
                not source_ascii_path.exists()
                or source_ascii_path.read_text().strip("\n") != source_ascii
            ):
                issues.append(f"{task_id}: source.ascii mismatch")
            source_png = task_dir / "source.png"
            if not source_png.exists() or source_png.stat().st_size == 0:
                issues.append(f"{task_id}: missing or empty source.png")

    task_dirs = sorted(
        path
        for path in tasks_root.rglob("*")
        if path.is_dir() and path.name.count(".") == 1
    )
    for task_dir in task_dirs:
        if task_dir not in expected_dirs:
            issues.append(f"unexpected task directory: {task_dir}")

    if issues:
        for issue in issues:
            print(issue)
        return 1

    print(f"Audit passed for {len(tasks)} tasks.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks-root", default="tasks")
    parser.add_argument("--data-dir", default="scripts/benchmark/data")
    args = parser.parse_args()
    raise SystemExit(audit(Path(args.tasks_root), Path(args.data_dir)))


if __name__ == "__main__":
    main()
