#!/usr/bin/env python3
"""Render benchmark ASCII diagrams to diagram-only PNG images."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.rendered.render import render


def render_all(tasks_root: Path) -> None:
    """Render every *.ascii file under tasks_root to a sibling .png."""
    ascii_files = sorted(tasks_root.rglob("*.ascii"))
    if not ascii_files:
        raise FileNotFoundError(f"No .ascii files found under {tasks_root}")

    for ascii_file in ascii_files:
        render(ascii_file, ascii_file.with_suffix(".png"))


def main() -> None:
    """CLI entrypoint: render every task's reference/source .ascii file to a sibling .png."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tasks-root",
        default="tasks",
        help="Directory containing benchmark task folders",
    )
    args = parser.parse_args()
    render_all(Path(args.tasks_root))


if __name__ == "__main__":
    main()
