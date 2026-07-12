#!/usr/bin/env python3
"""
L1 Structural Checker for TermDraw-Bench.
Scores a model's ASCII output against task assertions.
Returns a score 0.0-1.0.
"""
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List


@dataclass
class Assertions:
    required_labels: List[str] = field(default_factory=list)
    forbidden_labels: List[str] = field(default_factory=list)
    entity_count: int = 0
    required_edges: list = field(default_factory=list)
    required_edge_labels: List[str] = field(default_factory=list)
    preserved_elements: List[str] = field(default_factory=list)


def load_assertions(path: str) -> Assertions:
    data = json.loads(Path(path).read_text())
    return Assertions(**{k: v for k, v in data.items()
                         if k in Assertions.__dataclass_fields__})


def box_integrity(lines: List[str]) -> float:
    """Check that all detected boxes have correct corners and consistent widths."""
    # Find all '+' positions
    corners = [(r, c) for r, line in enumerate(lines)
               for c, ch in enumerate(line) if ch == '+']
    if not corners:
        return 0.0
    # Find candidate boxes: pairs of rows where '+' align in same columns
    scores = []
    col_set = {}
    for (r, c) in corners:
        col_set.setdefault(c, []).append(r)
    # For each pair of corner columns, check if there are matching row pairs
    cols = sorted(col_set.keys())
    found_box = False
    for i, c1 in enumerate(cols):
        for c2 in cols[i+1:]:
            shared_rows = set(col_set[c1]) & set(col_set[c2])
            if len(shared_rows) >= 2:
                row_pairs = sorted(shared_rows)
                for ri in range(len(row_pairs)-1):
                    r1, r2 = row_pairs[ri], row_pairs[ri+1]
                    # Check top wall: all chars between c1 and c2 on row r1 are '-' or '+'
                    top = lines[r1][c1:c2+1] if c2 < len(lines[r1]) else ""
                    bot = lines[r2][c1:c2+1] if c2 < len(lines[r2]) else ""
                    top_ok = all(ch in '-+' for ch in top)
                    bot_ok = all(ch in '-+' for ch in bot)
                    # Check side walls
                    walls_ok = True
                    for rm in range(r1+1, r2):
                        row = lines[rm]
                        if c1 >= len(row) or row[c1] != '|':
                            walls_ok = False
                        if c2 >= len(row) or row[c2] != '|':
                            walls_ok = False
                    # Width consistency
                    widths = [len(lines[r]) for r in range(r1, r2+1)
                              if r < len(lines)]
                    width_ok = (max(widths) - min(widths)) <= 1 if widths else False
                    score = (top_ok + bot_ok + walls_ok + width_ok) / 4
                    scores.append(score)
                    found_box = True
    return sum(scores) / len(scores) if scores else 0.0


def label_recall(output: str, required: List[str]) -> float:
    if not required:
        return 1.0
    found = sum(1 for lbl in required
                if lbl.lower() in output.lower())
    return found / len(required)


def label_absent(output: str, forbidden: List[str]) -> float:
    if not forbidden:
        return 1.0
    absent = sum(1 for lbl in forbidden
                 if lbl.lower() not in output.lower())
    return absent / len(forbidden)


def entity_count_score(lines: List[str], expected: int) -> float:
    if expected == 0:
        return 1.0
    # Count distinct closed boxes (top-left corners)
    corners = set()
    for r, line in enumerate(lines):
        for c, ch in enumerate(line):
            if ch == '+':
                # Check if this is a top-left corner
                right_ok = c+1 < len(line) and line[c+1] == '-'
                down_ok  = r+1 < len(lines) and c < len(lines[r+1]) and lines[r+1][c] == '|'
                if right_ok and down_ok:
                    corners.add((r, c))
    count = len(corners)
    return max(0.0, 1.0 - abs(count - expected) / max(expected, 1))


def edge_presence(output: str, edges: list) -> float:
    if not edges:
        return 1.0
    # For each required edge, check that both labels appear and there are
    # connector characters between their approximate positions
    connectors = set('-|><^v+/\\')
    found = 0
    for edge in edges:
        src, tgt = edge.get("from", ""), edge.get("to", "")
        if src.lower() in output.lower() and tgt.lower() in output.lower():
            # Check that connector characters exist somewhere between them
            # (simplified: just check both labels present + connectors exist)
            has_connectors = any(ch in output for ch in connectors)
            if has_connectors:
                found += 1
    return found / len(edges)


def edge_label_presence(output: str, edge_labels: List[str]) -> float:
    if not edge_labels:
        return 1.0
    found = sum(1 for lbl in edge_labels if lbl.lower() in output.lower())
    return found / len(edge_labels)


def format_compliance(output: str) -> float:
    has_plus  = '+' in output
    has_dash  = '-' in output
    has_pipe  = '|' in output
    return 1.0 if (has_plus and has_dash and has_pipe) else 0.0


def score(output: str, assertions: Assertions) -> dict:
    lines = output.splitlines()
    b  = box_integrity(lines)
    l  = label_recall(output, assertions.required_labels)
    fl = label_absent(output, assertions.forbidden_labels)
    e  = entity_count_score(lines, assertions.entity_count)
    r  = edge_presence(output, assertions.required_edges)
    el = edge_label_presence(output, assertions.required_edge_labels)
    f  = format_compliance(output)
    # Weights
    total = (b  * 0.25 +
             l  * 0.20 +
             fl * 0.10 +
             e  * 0.15 +
             r  * 0.15 +
             el * 0.10 +
             f  * 0.05)
    return {
        "box_integrity": round(b, 3),
        "label_recall": round(l, 3),
        "label_absent": round(fl, 3),
        "entity_count": round(e, 3),
        "edge_presence": round(r, 3),
        "edge_label_presence": round(el, 3),
        "format_compliance": round(f, 3),
        "L1_total": round(total, 3)
    }


if __name__ == "__main__":
    import sys
    output_text = Path(sys.argv[1]).read_text()
    assertions  = load_assertions(sys.argv[2])
    result = score(output_text, assertions)
    print(json.dumps(result, indent=2))
