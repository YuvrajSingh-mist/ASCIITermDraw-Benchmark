#!/usr/bin/env python3
"""Render all .ascii files in tasks/ to diagram-only .png images."""
import subprocess
import sys
import tempfile
from pathlib import Path


def render_ascii(ascii_file: Path, png_file: Path) -> None:
    subprocess.run([sys.executable, "scripts/render.py",
                    str(ascii_file), str(png_file)], check=True)


for ascii_file in sorted(Path("tasks").rglob("*.ascii")):
    png_file = ascii_file.with_suffix(".png")
    render_ascii(ascii_file, png_file)

c3_example = """+---------+     +---------+
| Alpha   |---->|  Beta   |
+---------+     +---------+
"""

with tempfile.NamedTemporaryFile("w", suffix=".ascii", delete=False) as tmp:
    tmp.write(c3_example)
    temp_path = Path(tmp.name)

try:
    render_ascii(temp_path, Path("oneshot/c3_example.png"))
finally:
    temp_path.unlink(missing_ok=True)
