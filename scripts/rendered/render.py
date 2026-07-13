#!/usr/bin/env python3
"""Render an ASCII file to a diagram-only PNG via Playwright."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
NODE_RENDERER = REPO_ROOT / "scripts" / "rendered" / "render_ascii.mjs"


def render(ascii_path: str | Path, out_path: str | Path) -> None:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ascii_path", help="Path to the input .ascii file")
    parser.add_argument("out_path", help="Path to the output .png file")
    args = parser.parse_args()
    render(args.ascii_path, args.out_path)


if __name__ == "__main__":
    main()
