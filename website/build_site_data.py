#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = ROOT / "tasks"
OUT = ROOT / "website" / "site_data.json"

CATEGORY_META = {
    "1": {
        "dir": "box-layout-basics",
        "name": "Box Layout Basics",
        "description": "Single boxes, rows, columns, arrows, lanes, and spacing-sensitive ASCII layout tasks.",
    },
    "2": {
        "dir": "network-topology-diagrams",
        "name": "Network Topology Diagrams",
        "description": "Distributed systems, clusters, buses, data flows, and topology-heavy connection diagrams.",
    },
    "3": {
        "dir": "diagram-editing",
        "name": "Diagram Editing",
        "description": "Image-to-text edit tasks where a model must transform an existing ASCII diagram correctly.",
    },
    "4": {
        "dir": "software-architecture-diagrams",
        "name": "Software Architecture Diagrams",
        "description": "Canonical architecture sketches such as gateways, pipelines, feeds, rate limiters, and storage systems.",
    },
}


def title_from_judge(task_dir: Path) -> str:
    first_line = read_text(task_dir / "vlm_judge_prompt.txt").splitlines()[0].strip()
    if first_line.startswith("TASK:"):
        return first_line.replace("TASK:", "", 1).split("(Task", 1)[0].strip()
    return first_line


def preview_from_reference(task_dir: Path) -> str:
    lines = read_text(task_dir / "reference.ascii").splitlines()
    return "\n".join(lines[:6])


def read_text(path: Path) -> str:
    result = subprocess.run(
        ["/bin/cat", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def build() -> None:
    categories = []
    total_tasks = 0
    total_edit_tasks = 0
    for category_id, meta in CATEGORY_META.items():
        category_dir = TASKS_DIR / meta["dir"]
        tasks = []
        for task_dir in sorted(category_dir.iterdir(), key=lambda p: float(p.name)):
            if not task_dir.is_dir():
                continue
            has_source = (task_dir / "source.ascii").exists()
            if has_source:
                total_edit_tasks += 1
            tasks.append(
                {
                    "task_id": task_dir.name,
                    "title": title_from_judge(task_dir),
                    "prompt": read_text(task_dir / "prompt.txt").strip(),
                    "path": str(task_dir.relative_to(ROOT)),
                    "has_source": has_source,
                    "preview": preview_from_reference(task_dir),
                }
            )
        total_tasks += len(tasks)
        categories.append(
            {
                "id": category_id,
                "slug": meta["dir"],
                "name": meta["name"],
                "description": meta["description"],
                "count": len(tasks),
                "tasks": tasks,
            }
        )

    payload = {
        "title": "TermDraw-Bench",
        "summary": "Benchmark for ASCII diagram generation and editing.",
        "stats": {
            "task_count": total_tasks,
            "category_count": len(categories),
            "edit_task_count": total_edit_tasks,
            "rendered_reference_count": total_tasks,
        },
        "categories": categories,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    build()
