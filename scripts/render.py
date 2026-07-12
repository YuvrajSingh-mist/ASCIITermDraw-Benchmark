#!/usr/bin/env python3
"""Render an ASCII .ascii file to a diagram-only PNG image via Playwright."""
import subprocess
import sys

def render(ascii_path: str, out_path: str):
    subprocess.run(
        ["node", "scripts/renderers/render_ascii.mjs", ascii_path, out_path],
        check=True,
    )

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
