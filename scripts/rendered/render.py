#!/usr/bin/env python3
"""Render an ASCII file to a diagram-only PNG via Playwright."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def _find_repo_root() -> Path:
    """Walk up from this file until we find pyproject.toml — the real project root."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root (no pyproject.toml found up to 10 levels).")


REPO_ROOT = _find_repo_root()
NODE_RENDERER = REPO_ROOT / "scripts" / "rendered" / "render_ascii.mjs"


def render(ascii_path: str | Path, out_path: str | Path) -> None:
    """Render a single .ascii file to a PNG by shelling out to the Node/Playwright renderer."""
    ascii_file = Path(ascii_path).resolve()
    output_file = Path(out_path).resolve()

    if not ascii_file.exists():
        raise FileNotFoundError(f"ASCII input not found: {ascii_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["node", str(NODE_RENDERER), str(ascii_file), str(output_file)],
            cwd=REPO_ROOT,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Node.js is required for PNG rendering. Install Node, run `npm install`, "
            "then `npx playwright install chromium`."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Playwright PNG rendering failed. Make sure dependencies are installed with "
            "`npm install` and `npx playwright install chromium`."
        ) from exc


def main() -> None:
    """CLI entrypoint: render a single .ascii file to a .png given as positional args."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ascii_path", help="Path to the input .ascii file")
    parser.add_argument("out_path", help="Path to the output .png file")
    args = parser.parse_args()
    render(args.ascii_path, args.out_path)


if __name__ == "__main__":
    main()
