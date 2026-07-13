from __future__ import annotations

import json
from pathlib import Path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = content.rstrip("\n") + "\n"
    if path.exists() and path.read_text() == normalized:
        return
    path.write_text(normalized)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = json.dumps(data, indent=2) + "\n"
    if path.exists() and path.read_text() == normalized:
        return
    path.write_text(normalized)
