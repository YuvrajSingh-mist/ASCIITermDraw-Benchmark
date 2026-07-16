#!/usr/bin/env python3
"""
Run TermDraw-Bench L2 judging with Instructor + Pydantic.

This is useful for smaller synchronous runs where you want automatic
validation/retry behavior. Fireworks batch judging remains the scalable path.
"""
from __future__ import annotations

import argparse
import base64
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

from typing import TYPE_CHECKING

from typing import Any

try:
    from pydantic import BaseModel, ConfigDict
except ModuleNotFoundError as _PYDANTIC_ERROR:
    BaseModel = object

    def ConfigDict(**_: Any) -> dict[str, Any]:
        return {}
else:
    _PYDANTIC_ERROR = None

from scripts.lib.fireworks_api import iter_task_dirs, require_env
from scripts.lib.fireworks_api import create_instructor_client

if TYPE_CHECKING:
    import instructor
    from openai import OpenAI


class StructuralObservations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_labels_present: list[str]
    entity_count_observed: int
    required_edges_present: list[dict[str, str]]
    required_edge_labels_present: list[str] = []
    preserved_elements_present: list[str] = []


class SemanticsObservations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semantics_score: float
    connections_correct: int
    text_inside_nodes_correct: int
    text_centered_in_nodes: int
    layout_matches_prompt: int
    labels_spelled_correct: int
    arrows_cleanly_aligned: int


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    structural_observations: StructuralObservations
    semantics: SemanticsObservations
    reason: str


SYSTEM_PROMPT = (
    "You are a strict ASCII-diagram benchmark judge. "
    "Return a valid JudgeResult object. "
    "Structural judging means extracting factual evidence about the candidate diagram: "
    "which required labels are present, how many entities are present, which required "
    "edges are present, and for editing tasks which required edge labels and preserved "
    "elements are present. Report only those observations and let the harness compare "
    "them against the task assertions to compute the structural score. "
    "Semantic judging means evaluating whether the candidate diagram actually follows "
    "the requested architecture and visual intent: connections are correct, node text "
    "is correct, text is centered, labels are spelled correctly, arrows are cleanly "
    "aligned, and the overall layout matches the prompt and reference image. "
    "Return both the binary semantic rubric fields and a direct `semantics_score` from "
    "0.0 to 1.0 based on that semantic judgment. "
    "Keep `reason` concise."
)

ROOT = Path(__file__).resolve().parents[2]
SHARED_JUDGE_CONTRACT_PATH = ROOT / "scripts" / "judge" / "shared_judge_contract.txt"


def encode_image_data_url(image_path: Path) -> str:
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def load_shared_judge_contract() -> str:
    return SHARED_JUDGE_CONTRACT_PATH.read_text().strip()


def render_ascii_to_png(ascii_text: str, output_path: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".ascii", delete=False) as tmp:
        tmp.write(ascii_text.rstrip("\n") + "\n")
        temp_ascii_path = Path(tmp.name)
    try:
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().parents[1] / "rendered" / "render.py"),
                str(temp_ascii_path),
                str(output_path),
            ],
            check=True,
            timeout=60,
        )
    finally:
        temp_ascii_path.unlink(missing_ok=True)


def normalize_label_set(items: list[str]) -> set[str]:
    return {item.strip().lower() for item in items if item.strip()}


def normalize_edge_set(edges: list[dict[str, str]]) -> set[tuple[str, str]]:
    normalized: set[tuple[str, str]] = set()
    for edge in edges:
        src = edge.get("from", "").strip().lower()
        dst = edge.get("to", "").strip().lower()
        if src and dst:
            normalized.add((src, dst))
    return normalized


def structural_score_from_observations(
    task_dir: Path,
    observations: StructuralObservations,
) -> tuple[float, dict[str, float]]:
    import json

    assertions = json.loads((task_dir / "assertions.json").read_text())
    components: dict[str, float] = {}

    required_labels = assertions.get("required_labels", [])
    required_labels_present = normalize_label_set(observations.required_labels_present)
    if required_labels:
        components["required_labels"] = 1.0 if normalize_label_set(required_labels) <= required_labels_present else 0.0

    expected_entity_count = assertions.get("entity_count", 0)
    components["entity_count"] = 1.0 if observations.entity_count_observed == expected_entity_count else 0.0

    required_edges = assertions.get("required_edges", [])
    if required_edges:
        components["required_edges"] = 1.0 if normalize_edge_set(required_edges) <= normalize_edge_set(observations.required_edges_present) else 0.0

    editing = assertions.get("editing", {})
    required_edge_labels = assertions.get(
        "required_edge_labels",
        editing.get("required_edge_labels", []),
    )
    if required_edge_labels:
        components["required_edge_labels"] = 1.0 if normalize_label_set(required_edge_labels) <= normalize_label_set(observations.required_edge_labels_present) else 0.0

    preserved_elements = assertions.get(
        "preserved_elements",
        editing.get("preserved_elements", []),
    )
    if preserved_elements:
        components["preserved_elements"] = 1.0 if normalize_label_set(preserved_elements) <= normalize_label_set(observations.preserved_elements_present) else 0.0

    if not components:
        return 0.0, {}
    return sum(components.values()) / len(components), components


def semantics_score_from_observations(observations: SemanticsObservations) -> tuple[float, dict[str, float | int]]:
    semantics_score = max(0.0, min(1.0, float(observations.semantics_score)))
    components = {
        "semantics_score": semantics_score,
        "connections_correct": 1 if observations.connections_correct else 0,
        "text_inside_nodes_correct": 1 if observations.text_inside_nodes_correct else 0,
        "text_centered_in_nodes": 1 if observations.text_centered_in_nodes else 0,
        "layout_matches_prompt": 1 if observations.layout_matches_prompt else 0,
        "labels_spelled_correct": 1 if observations.labels_spelled_correct else 0,
        "arrows_cleanly_aligned": 1 if observations.arrows_cleanly_aligned else 0,
    }
    return semantics_score, components


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def save_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run(
    *,
    model: str,
    tasks_dir: str,
    outputs_dir: str,
    results_path: str,
    max_retries: int,
) -> None:
    if _PYDANTIC_ERROR is not None:
        raise RuntimeError(
            "Missing Python dependency `pydantic`. "
            "Install project dependencies with `uv sync`."
        ) from _PYDANTIC_ERROR

    client = create_instructor_client(require_env("FIREWORKS_API_KEY"))

    tasks = Path(tasks_dir)
    outputs = Path(outputs_dir)
    results = Path(results_path)

    existing = load_csv_rows(results)
    rows_by_task = {row["task_id"]: row for row in existing if row.get("task_id")}

    for task_dir in iter_task_dirs(tasks):
        task_id = task_dir.name
        output_file = outputs / f"{task_id}.txt"
        if not output_file.exists():
            print(f"Skipping {task_id}: missing model output")
            continue

        output_text = output_file.read_text().strip()
        prompt = (task_dir / "vlm_judge_prompt.txt").read_text().replace(
            "{model_output}",
            output_text,
        )
        prompt = f"{prompt}\n\n{load_shared_judge_contract()}"
        user_content: str | list[dict[str, Any]] = prompt
        if (task_dir / "source.ascii").exists():
            source_png = task_dir / "source.png"
            reference_png = task_dir / "reference.png"
            rendered_dir = outputs / "judge_rendered"
            rendered_dir.mkdir(parents=True, exist_ok=True)
            output_png = rendered_dir / f"{task_id}.png"
            render_ascii_to_png(output_text, output_png)
            user_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": encode_image_data_url(source_png)}},
                {"type": "image_url", "image_url": {"url": encode_image_data_url(reference_png)}},
                {"type": "image_url", "image_url": {"url": encode_image_data_url(output_png)}},
            ]
        result = client.chat.completions.create(
            model=model,
            response_model=JudgeResult,
            max_retries=max_retries,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        row = rows_by_task.setdefault(task_id, {"task_id": task_id})
        structural_score, structural_components = structural_score_from_observations(
            task_dir,
            result.structural_observations,
        )
        semantics_score, semantics_components = semantics_score_from_observations(
            result.semantics,
        )
        total_score = structural_score + semantics_score
        passed = structural_score >= 0.9999 and semantics_score >= 0.9999

        row["structural_score"] = f"{structural_score:.4f}"
        row["semantics_score"] = f"{semantics_score:.4f}"
        row["judge_score"] = f"{total_score:.4f}"
        row["L2_score"] = f"{total_score:.4f}"
        row["L2_passed"] = str(passed).lower()
        row["L2_reason"] = result.reason
        row["assertion_score"] = row.get("L1_total", "")
        row["final_score"] = f"{total_score:.4f}"
        for key, value in structural_components.items():
            row[f"structural_{key}"] = f"{value:.4f}"
        for key, value in semantics_components.items():
            if isinstance(value, float):
                row[f"semantics_{key}"] = f"{value:.4f}"
            else:
                row[f"semantics_{key}"] = str(value)

        judge_dir = outputs / "judge_json"
        judge_dir.mkdir(parents=True, exist_ok=True)
        (judge_dir / f"{task_id}.json").write_text(result.model_dump_json(indent=2) + "\n")
        print(f"Judged {task_id}")

    merged_rows = [rows_by_task[task_dir.name] for task_dir in iter_task_dirs(tasks)]
    save_csv_rows(results, merged_rows)
    print(f"Updated {results}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Fireworks model path")
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()
    run(
        model=args.model,
        tasks_dir=args.tasks,
        outputs_dir=args.outputs,
        results_path=args.results,
        max_retries=args.max_retries,
    )


if __name__ == "__main__":
    main()
