#!/usr/bin/env python3
"""Judge result schema, structural/semantic scoring, and results-CSV helpers shared by the DeepEval judge pipeline (geval_metrics.py, geval_support.py, run_geval_judge.py)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class StructuralObservations(BaseModel):
    """Factual evidence about the candidate diagram, as reported by the judge model."""

    model_config = ConfigDict(extra="forbid")

    required_labels_present: list[str]
    entity_count_observed: int
    required_edges_present: list[dict[str, str]]
    required_edge_labels_present: list[str] = []
    preserved_elements_present: list[str] = []


class SemanticsObservations(BaseModel):
    """The judge model's semantic rubric verdict plus its own direct 0.0-1.0 score."""

    model_config = ConfigDict(extra="forbid")

    semantics_score: float
    connections_correct: int
    text_inside_nodes_correct: int
    text_centered_in_nodes: int
    layout_matches_prompt: int
    labels_spelled_correct: int
    arrows_cleanly_aligned: int


class JudgeResult(BaseModel):
    """The full structured response a judge call must return.

    `reason` is declared first (and must be written first in the JSON
    response — see the per-task prompt's response-schema example) so the
    model reasons through the evidence before committing to scores, rather
    than writing scores first and rationalizing them after the fact.
    """

    model_config = ConfigDict(extra="forbid")

    reason: str
    structural_observations: StructuralObservations
    semantics: SemanticsObservations


SYSTEM_PROMPT = (
    "You are a strict, consistent ASCII-diagram benchmark judge. "
    "Return a valid JudgeResult object. "
    "Write `reason` first: think step by step about what you actually observe in the "
    "images before deciding any score. Do not decide the scores first and rationalize "
    "them afterward. "
    "Structural judging means extracting factual evidence about the candidate diagram: "
    "which required labels are present, how many entities are present, which required "
    "edges are present, and for editing tasks, all of what is previously mentioned AND which required edge labels and preserved "
    "elements are present. Report only those observations and let the harness compare "
    "them against the task assertions to compute the structural score. "
    "Semantic judging means evaluating whether the candidate diagram actually follows "
    "the requested architecture and visual intent: connections are correct, node text "
    "is correct, text is centered, labels are spelled correctly, arrows are cleanly "
    "aligned, and the overall layout matches the prompt and reference image. "
    "Judge only against the stated rubric and task prompt — do not reward a diagram for "
    "being more elaborate, longer, or more visually elaborate than what was asked for, and "
    "do not penalize a correct, minimal diagram for being simple. Apply the same standard "
    "regardless of how confident or verbose the diagram or its labels look. "
    "Return both the binary semantic rubric fields and a direct `semantics_score` from "
    "0.0 to 1.0 based on that semantic judgment. "
    "Keep `reason` concise but concrete — cite what you actually saw, not generic praise "
    "or criticism."
)

ROOT = Path(__file__).resolve().parents[2]
SHARED_JUDGE_CONTRACT_PATH = ROOT / "scripts" / "judge" / "shared_judge_contract.txt"


def load_shared_judge_contract() -> str:
    """Read the JSON-shape/response-contract text appended to every task's judge prompt."""
    return SHARED_JUDGE_CONTRACT_PATH.read_text().strip()


def normalize_label_set(items: list[str]) -> set[str]:
    """Lowercase and strip a list of labels into a set, for order/case-insensitive comparison."""
    return {item.strip().lower() for item in items if item.strip()}


def normalize_edge_set(edges: list[dict[str, str]]) -> set[tuple[str, str]]:
    """Turn a list of {"from", "to"} edge dicts into a set of lowercased (from, to) tuples."""
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
    """Compare the judge's structural observations against task_dir/assertions.json and average the binary component checks."""
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
    """Clamp the judge's semantics_score to [0, 1] and collect the binary rubric fields alongside it."""
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
    """Read a results CSV into a list of row dicts, or an empty list if it doesn't exist yet."""
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def save_csv_rows(path: Path, rows: list[dict[str, str]]) -> None:
    """Write rows back to a results CSV, taking the column order from the union of keys seen."""
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
