#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

from scripts.benchmark.io import write_json
from scripts.benchmark.prompts import strip_task_prompt_suffix
from scripts.benchmark.tasks import TASK_CATEGORY_DIRS
from scripts.lib.fireworks_api import iter_task_dirs


ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "tasks"
DATA_DIR = ROOT / "scripts" / "benchmark" / "data"


def _task_sort_key(task_id: str) -> tuple[int, int]:
    major, minor = task_id.split(".", 1)
    return int(major), int(minor)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _read_text(path: Path) -> str:
    return path.read_text().rstrip("\n")


def _snapshot_task(task_dir: Path) -> dict:
    task_id = task_dir.name
    snapshot = {
        "prompt": strip_task_prompt_suffix(
            task_id,
            _read_text(task_dir / "prompt.txt"),
        ),
        "reference": _read_text(task_dir / "reference.ascii"),
        "assertions": _load_json(task_dir / "assertions.json"),
    }
    source_path = task_dir / "source.ascii"
    if source_path.exists():
        snapshot["source"] = _read_text(source_path)
    return snapshot


def snapshot_category(category: str, slug: str) -> None:
    category_dir = TASKS_DIR / slug
    payload: OrderedDict[str, dict] = OrderedDict()
    for task_dir in iter_task_dirs(category_dir):
        payload[task_dir.name] = _snapshot_task(task_dir)
    write_json(DATA_DIR / f"category_{category}.json", payload)


def main() -> None:
    for category, slug in TASK_CATEGORY_DIRS.items():
        snapshot_category(category, slug)


if __name__ == "__main__":
    main()
