#!/usr/bin/env python3
"""Render benchmark ASCII diagrams to diagram-only PNG images."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.rendered.render import render


C3_EXAMPLE = (
    "+---------+     +---------+\n"
    "| Alpha   |---->|  Beta   |\n"
    "+---------+     +---------+\n"
)


def render_all(tasks_root: Path, oneshot_png: Path) -> None:
    """Render every *.ascii file under tasks_root to a sibling .png, plus a fixed example diagram to oneshot_png."""
    ascii_files = sorted(tasks_root.rglob("*.ascii"))
    if not ascii_files:
        raise FileNotFoundError(f"No .ascii files found under {tasks_root}")

    for ascii_file in ascii_files:
        render(ascii_file, ascii_file.with_suffix(".png"))

    oneshot_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".ascii", delete=False) as tmp:
        tmp.write(C3_EXAMPLE)
        temp_path = Path(tmp.name)

    try:
        render(temp_path, oneshot_png)
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> None:
    """CLI entrypoint: render every task's reference/source .ascii file plus the oneshot example PNG."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tasks-root",
        default="tasks",
        help="Directory containing benchmark task folders",
    )
    parser.add_argument(
        "--oneshot-png",
        default="oneshot/c3_example.png",
        help="Path to the generated one-shot PNG example",
    )
    args = parser.parse_args()
    render_all(Path(args.tasks_root), Path(args.oneshot_png))


if __name__ == "__main__":
    main()
