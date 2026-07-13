#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path
from textwrap import dedent

from scripts.benchmark.io import write_json, write_text
from scripts.benchmark.oneshots import ONESHOT_EXAMPLES
from scripts.benchmark.prompts import (
    build_judge_prompt,
    finalize_task_prompt,
    normalize_assertions,
)
from scripts.benchmark.tasks import (
    TASK_CATEGORY_DIRS,
    load_tasks,
    task_difficulty_bucket,
)


ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "tasks"
ONESHOT_DIR = ROOT / "oneshot"
TASK_DATA_DIR = ROOT / "scripts" / "benchmark" / "data"


def render_oneshots() -> None:
    for name, content in ONESHOT_EXAMPLES.items():
        write_text(ONESHOT_DIR / name, dedent(content).strip("\n"))


def render_tasks() -> None:
    tasks = load_tasks(TASK_DATA_DIR)
    expected_dirs: set[Path] = set()

    for task_id, data in tasks.items():
        category = task_id.split(".", 1)[0]
        task_dir = (
            TASKS_DIR
            / TASK_CATEGORY_DIRS.get(category, category)
            / task_difficulty_bucket(task_id)
            / task_id
        )
        expected_dirs.add(task_dir)
        assertions = normalize_assertions(task_id, data["assertions"])
        prompt = finalize_task_prompt(task_id, data["prompt"])
        judge_prompt = build_judge_prompt(
            task_id,
            prompt,
            assertions,
            data.get("source"),
        )

        write_text(task_dir / "prompt.txt", prompt)
        write_text(task_dir / "reference.ascii", dedent(data["reference"]).strip("\n"))
        write_json(task_dir / "assertions.json", assertions)
        write_text(task_dir / "vlm_judge_prompt.txt", judge_prompt)
        if data.get("source") is not None:
            write_text(task_dir / "source.ascii", dedent(data["source"]).strip("\n"))

    for category_dir in TASKS_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        for path in sorted(category_dir.rglob("*"), reverse=True):
            if path.is_dir() and path.name.count(".") == 1 and path not in expected_dirs:
                shutil.rmtree(path)


def main() -> None:
    render_oneshots()
    render_tasks()


if __name__ == "__main__":
    main()
