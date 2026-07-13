from __future__ import annotations

import json
from pathlib import Path


TASK_CATEGORY_DIRS = {
    "1": "box-layout-basics",
    "2": "network-topology-diagrams",
    "3": "diagram-editing",
    "4": "software-architecture-diagrams",
}

TASK_DIFFICULTY_DIRS = {
    "easy": range(1, 11),
    "medium": range(11, 16),
    "hard": range(16, 21),
}


def _task_sort_key(task_id: str) -> tuple[int, int]:
    major, minor = task_id.split(".", 1)
    return int(major), int(minor)


def task_difficulty_bucket(task_id: str) -> str:
    _, minor = _task_sort_key(task_id)
    for bucket, task_range in TASK_DIFFICULTY_DIRS.items():
        if minor in task_range:
            return bucket
    raise ValueError(f"Task id {task_id} does not map to an expected difficulty bucket.")


def load_tasks(data_dir: Path) -> dict[str, dict]:
    tasks: dict[str, dict] = {}
    for json_path in sorted(data_dir.glob("category_*.json")):
        tasks.update(json.loads(json_path.read_text()))
    return dict(sorted(tasks.items(), key=lambda item: _task_sort_key(item[0])))
