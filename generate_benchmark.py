#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).parent
TASKS_DIR = ROOT / "tasks"
ONESHOT_DIR = ROOT / "oneshot"
SCRIPTS_DIR = ROOT / "scripts"
TASK_CATEGORY_DIRS = {
    "1": "box-layout-basics",
    "2": "network-topology-diagrams",
    "3": "diagram-editing",
    "4": "software-architecture-diagrams",
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip("\n") + "\n")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


SCRIPT_RENDER = """#!/usr/bin/env python3
\"\"\"Render an ASCII .ascii file to a diagram-only PNG image via Playwright.\"\"\"
import subprocess
import sys

def render(ascii_path: str, out_path: str):
    subprocess.run(
        ["node", "scripts/renderers/render_ascii.mjs", ascii_path, out_path],
        check=True,
    )

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
"""

SCRIPT_RENDER_ALL = """#!/usr/bin/env python3
\"\"\"Render all .ascii files in tasks/ to diagram-only .png images.\"\"\"
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

c3_example = \"+---------+     +---------+\\n| Alpha   |---->|  Beta   |\\n+---------+     +---------+\\n\"

with tempfile.NamedTemporaryFile("w", suffix=".ascii", delete=False) as tmp:
    tmp.write(c3_example)
    temp_path = Path(tmp.name)

try:
    render_ascii(temp_path, Path("oneshot/c3_example.png"))
finally:
    temp_path.unlink(missing_ok=True)
"""

SCRIPT_RENDER_ASCII_MJS = """import { readFile } from "node:fs/promises";
import { chromium } from "playwright";

const input = process.argv[2];
const output = process.argv[3];

if (!input || !output) {
  console.error("Usage: node scripts/renderers/render_ascii.mjs <input.ascii> <output.png>");
  process.exit(1);
}

const text = await readFile(input, "utf8");

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ deviceScaleFactor: 2 });

const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <style>
      html, body {
        margin: 0;
        padding: 0;
        background: #ffffff;
      }
      body {
        display: inline-block;
        padding: 24px 28px;
        font-family: Menlo, Monaco, "Cascadia Mono", "SF Mono", Consolas, monospace;
      }
      pre {
        margin: 0;
        color: #111827;
        background: #ffffff;
        font-size: 22px;
        line-height: 1.2;
        letter-spacing: 0;
        white-space: pre;
      }
    </style>
  </head>
  <body>
    <pre id="diagram"></pre>
    <script>
      document.getElementById("diagram").textContent = ${JSON.stringify(text)};
    </script>
  </body>
</html>`;

await page.setContent(html, { waitUntil: "load" });
await page.locator("pre").screenshot({ path: output });
await browser.close();
console.log(`Rendered ${input} -> ${output}`);
"""

SCRIPT_CHECKER = """#!/usr/bin/env python3
\"\"\"
L1 Structural Checker for TermDraw-Bench.
Scores a model's ASCII output against task assertions.
Returns a score 0.0-1.0.
\"\"\"
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
    \"\"\"Check that all detected boxes have correct corners and consistent widths.\"\"\"
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
    connectors = set('-|><^v+/\\\\')
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
"""

SCRIPT_EVAL = """#!/usr/bin/env python3
\"\"\"
TermDraw-Bench Evaluation Harness.

Usage:
    python scripts/eval.py --outputs outputs/model_name/ --tasks tasks/ --results results.csv

Expects outputs/model_name/ to contain files named {task_id}.txt
(e.g. 1.1.txt, 2.3.txt, 3.7.txt, 4.11.txt)

For C3 tasks, model output is still plain text (ASCII diagram).
The image was the input; the output is always text.
\"\"\"
import csv
import json
import argparse
from pathlib import Path
from lib.checker import score, load_assertions

def run_eval(outputs_dir: str, tasks_dir: str, results_path: str):
    outputs = Path(outputs_dir)
    tasks   = Path(tasks_dir)
    rows    = []

    for task_dir in sorted(tasks.iterdir()):
        task_id = task_dir.name
        output_file = outputs / f"{task_id}.txt"
        assertions_file = task_dir / "assertions.json"

        if not output_file.exists():
            print(f"MISSING output: {task_id}")
            continue
        if not assertions_file.exists():
            print(f"MISSING assertions: {task_id}")
            continue

        output_text = output_file.read_text()
        assertions  = load_assertions(str(assertions_file))
        l1_result   = score(output_text, assertions)

        row = {"task_id": task_id, **l1_result, "L2_score": "", "final_score": ""}
        rows.append(row)
        print(f"{task_id}: L1={l1_result['L1_total']:.3f}")

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(results_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\\nResults written to {results_path}")
        avg = sum(r["L1_total"] for r in rows) / len(rows)
        print(f"Mean L1: {avg:.3f} across {len(rows)} tasks")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--outputs", required=True)
    p.add_argument("--tasks",   default="tasks")
    p.add_argument("--results", default="results.csv")
    args = p.parse_args()
    run_eval(args.outputs, args.tasks, args.results)
"""

SCRIPT_RUN_MODEL = """#!/usr/bin/env python3
\"\"\"
Run a model on all TermDraw-Bench tasks and save outputs.

Usage:
    python scripts/run_model.py \\
        --model Qwen/Qwen2.5-7B-Instruct \\
        --tasks tasks/ \\
        --outputs outputs/qwen2.5-7b/ \\
        --oneshot oneshot/

Reads tasks/{id}/prompt.txt and prepends the category oneshot example.
Saves model output to outputs/{model_name}/{task_id}.txt
\"\"\"
import argparse
from pathlib import Path

CATEGORY_ONESHOT = {
    "1": "oneshot/c1_example.txt",
    "2": "oneshot/c2_example.txt",
    "3": "oneshot/c3_example.txt",  # text version for non-vision models
    "4": "oneshot/c4_example.txt",
}

SYSTEM_PROMPT = (
    "You are a technical documentation assistant. "
    "Generate correct, well-formed ASCII diagrams using only standard "
    "ASCII characters: + - | > < ^ v / \\\\ . "
    "Output only the diagram. No explanation, no markdown fences."
)

def build_prompt(task_id: str, task_dir: Path, oneshot_dir: Path) -> str:
    category = task_id.split(".")[0]
    prompt_text = (task_dir / "prompt.txt").read_text().strip()
    oneshot_file = Path(oneshot_dir) / f"c{category}_example.txt"
    if oneshot_file.exists():
        oneshot = oneshot_file.read_text().strip()
        return f"{oneshot}\\n\\nNow complete the following:\\n\\n{prompt_text}\\n\\nOutput only the diagram."
    return f"{prompt_text}\\n\\nOutput only the diagram."

def run(model_name: str, tasks_dir: str, outputs_dir: str, oneshot_dir: str):
    from vllm import LLM, SamplingParams
    tasks   = Path(tasks_dir)
    outputs = Path(outputs_dir)
    outputs.mkdir(parents=True, exist_ok=True)

    llm = LLM(model=model_name, max_model_len=4096)
    params = SamplingParams(temperature=0.0, max_tokens=512)

    task_dirs = sorted(tasks.iterdir(), key=lambda p: (
        int(p.name.split(".")[0]), float(p.name)))

    prompts  = []
    task_ids = []
    for td in task_dirs:
        if not (td / "prompt.txt").exists():
            continue
        task_ids.append(td.name)
        prompts.append(build_prompt(td.name, td, oneshot_dir))

    # Batch inference
    outputs_list = llm.generate(
        [SYSTEM_PROMPT + "\\n\\n" + p for p in prompts], params)

    for task_id, out in zip(task_ids, outputs_list):
        text = out.outputs[0].text.strip()
        (outputs / f"{task_id}.txt").write_text(text)
        print(f"Done: {task_id}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model",   required=True)
    p.add_argument("--tasks",   default="tasks")
    p.add_argument("--outputs", required=True)
    p.add_argument("--oneshot", default="oneshot")
    args = p.parse_args()
    run(args.model, args.tasks, args.outputs, args.oneshot)
"""


TASKS = {
    "1.1": {
        "prompt": 'Draw a single ASCII box with the label "API Gateway" centered inside it.',
        "reference": """
+---------------+
|  API Gateway  |
+---------------+
""",
        "assertions": {
            "required_labels": ["API Gateway"],
            "forbidden_labels": [],
            "entity_count": 1,
            "required_edges": [],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        "judge": """
TASK: Single labeled box (Task 1.1)

The diagram should show exactly one closed ASCII box containing the label
"API Gateway".

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST (score each 1=correct, 0=wrong/missing):
1. box_closed: four `+` corners with `-` top/bottom and `|` sides
2. label_present: text "API Gateway" appears inside the box
3. single_box: only one box is drawn, no extra boxes
4. label_inside: label is between the walls, not outside the box

RESPOND in this JSON format only:
{"scores": {"box_closed": 0, "label_present": 0, "single_box": 0, "label_inside": 0}, "total": 0, "pass": false, "reason": "string"}
""",
    },
}


def add_task(task_id: str, *, prompt: str, reference: str, assertions: dict, judge: str, source: str | None = None) -> None:
    TASKS[task_id] = {
        "prompt": prompt,
        "reference": reference,
        "assertions": assertions,
        "judge": judge,
        "source": source,
    }


def populate_tasks() -> None:
    add_task(
        "1.2",
        prompt='Draw three boxes labeled "Input", "Process", "Output" connected left-to-right with arrows.',
        reference="""
+---------+     +-----------+     +----------+
|  Input  |---->|  Process  |---->|  Output  |
+---------+     +-----------+     +----------+
""",
        assertions={
            "required_labels": ["Input", "Process", "Output"],
            "forbidden_labels": [],
            "entity_count": 3,
            "required_edges": [{"from": "Input", "to": "Process"}, {"from": "Process", "to": "Output"}],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Horizontal chain (Task 1.2)

Three boxes "Input", "Process", "Output" connected left-to-right with arrows.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. three_boxes: exactly three closed boxes exist
2. input_label: "Input" label present
3. process_label: "Process" label present
4. output_label: "Output" label present
5. left_to_right_order: Input is leftmost, Output is rightmost
6. input_to_process_arrow: arrow connecting Input to Process
7. process_to_output_arrow: arrow connecting Process to Output

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.3",
        prompt='Draw four boxes stacked vertically: "Load Balancer", "App Server", "Cache", "Database". Connect them top-to-bottom with downward arrows.',
        reference="""
+-----------------+
|  Load Balancer  |
+-----------------+
         |
         v
+-----------------+
|   App Server    |
+-----------------+
         |
         v
+-----------------+
|      Cache      |
+-----------------+
         |
         v
+-----------------+
|    Database     |
+-----------------+
""",
        assertions={
            "required_labels": ["Load Balancer", "App Server", "Cache", "Database"],
            "forbidden_labels": [],
            "entity_count": 4,
            "required_edges": [
                {"from": "Load Balancer", "to": "App Server"},
                {"from": "App Server", "to": "Cache"},
                {"from": "Cache", "to": "Database"},
            ],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Vertical stack (Task 1.3)

Four boxes stacked top-to-bottom with downward arrows in this order:
Load Balancer → App Server → Cache → Database.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. four_boxes: four closed boxes exist
2. all_labels: all four labels present
3. correct_order: Load Balancer is topmost, Database is bottommost
4. three_arrows: three downward connectors between adjacent boxes
5. consistent_widths: all boxes have the same width (padded to match longest label)

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.4",
        prompt='Draw a two-column layout. Left column: one box labeled "Client". Right column: two stacked boxes labeled "Primary DB" on top and "Replica DB" below. Connect the Client to both DB boxes with arrows pointing right.',
        reference="""
+----------+        +------------+
|  Client  |------->| Primary DB |
+----------+        +------------+
      |
      +------------>| Replica DB |
                     +------------+
""",
        assertions={
            "required_labels": ["Client", "Primary DB", "Replica DB"],
            "forbidden_labels": [],
            "entity_count": 3,
            "required_edges": [{"from": "Client", "to": "Primary DB"}, {"from": "Client", "to": "Replica DB"}],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Two-column layout (Task 1.4)

Client on the left connects to Primary DB (top) and Replica DB (bottom) on the right.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. client_box: "Client" box exists
2. primary_db_box: "Primary DB" box exists
3. replica_db_box: "Replica DB" box exists
4. client_left: Client is to the left of both DB boxes
5. primary_above_replica: Primary DB is above Replica DB
6. client_to_primary: arrow from Client to Primary DB
7. client_to_replica: arrow from Client to Replica DB

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.5",
        prompt='Draw two boxes "Service A" and "Service B" side by side with a bidirectional arrow between them showing data flows both ways.',
        reference="""
+-----------+     +-----------+
| Service A |<--->| Service B |
+-----------+     +-----------+
""",
        assertions={
            "required_labels": ["Service A", "Service B"],
            "forbidden_labels": [],
            "entity_count": 2,
            "required_edges": [{"from": "Service A", "to": "Service B"}, {"from": "Service B", "to": "Service A"}],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Bidirectional arrows (Task 1.5)

Two boxes with arrows going both directions between them.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. two_boxes: two closed boxes exist
2. service_a: "Service A" label present
3. service_b: "Service B" label present
4. bidirectional: both `<` and `>` characters present in the connector (or two separate arrows shown)

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.6",
        prompt='Draw two boxes "Producer" and "Consumer" connected by a right-pointing arrow. Place the label "events" above the arrow line between the two boxes.',
        reference="""
                 events
+----------+  ----------->  +----------+
| Producer |                | Consumer |
+----------+                +----------+
""",
        assertions={
            "required_labels": ["Producer", "Consumer", "events"],
            "forbidden_labels": [],
            "entity_count": 2,
            "required_edges": [{"from": "Producer", "to": "Consumer"}],
            "required_edge_labels": ["events"],
            "preserved_elements": [],
        },
        judge="""
TASK: Labeled arrow (Task 1.6)

Producer → Consumer with "events" label above the arrow.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. producer_box: "Producer" box exists
2. consumer_box: "Consumer" box exists
3. arrow_present: arrow from Producer to Consumer
4. events_label: text "events" appears near the arrow, not inside a box

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.7",
        prompt='Draw one box "API Server" at the top. Below it, draw three boxes in a row: "Users DB", "Products DB", "Orders DB". Connect the API Server to each of the three boxes with downward arrows.',
        reference="""
                 +------------+
                 | API Server |
                 +------------+
                   |    |    |
                   v    v    v
+----------+   +-------------+   +-----------+
| Users DB |   | Products DB |   | Orders DB |
+----------+   +-------------+   +-----------+
""",
        assertions={
            "required_labels": ["API Server", "Users DB", "Products DB", "Orders DB"],
            "forbidden_labels": [],
            "entity_count": 4,
            "required_edges": [
                {"from": "API Server", "to": "Users DB"},
                {"from": "API Server", "to": "Products DB"},
                {"from": "API Server", "to": "Orders DB"},
            ],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Fan-out (Task 1.7)

API Server at top fans out to three DB boxes at the same level below it.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. api_server: "API Server" box exists
2. users_db: "Users DB" box exists
3. products_db: "Products DB" box exists
4. orders_db: "Orders DB" box exists
5. all_three_connections: API Server connects to all three DB boxes (not just one or two)
6. db_same_level: all three DB boxes are at approximately the same vertical position

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.8",
        prompt='Draw three boxes in a row at the top: "Web", "Mobile", "CLI". Below them, draw one box "GraphQL Gateway". Connect each of the three top boxes to the Gateway with downward arrows.',
        reference="""
+-------+    +--------+    +-------+
|  Web  |    | Mobile |    |  CLI  |
+-------+    +--------+    +-------+
     \           |           /
      \          |          /
       v         v         v
         +-----------------+
         | GraphQL Gateway |
         +-----------------+
""",
        assertions={
            "required_labels": ["Web", "Mobile", "CLI", "GraphQL Gateway"],
            "forbidden_labels": [],
            "entity_count": 4,
            "required_edges": [
                {"from": "Web", "to": "GraphQL Gateway"},
                {"from": "Mobile", "to": "GraphQL Gateway"},
                {"from": "CLI", "to": "GraphQL Gateway"},
            ],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Fan-in (Task 1.8)

Three source boxes (Web, Mobile, CLI) all connect down to one GraphQL Gateway box.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. web_box: "Web" exists
2. mobile_box: "Mobile" exists
3. cli_box: "CLI" exists
4. gateway_box: "GraphQL Gateway" exists
5. three_to_one: all three sources connect to the gateway (not just one or two)
6. gateway_below: gateway is below the three source boxes

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.9",
        prompt='Draw an ASCII box representing a database table called "users". Use a horizontal divider line inside the box to separate the table name (top section) from three fields listed below it: "id (PK)", "email", "created_at".',
        reference="""
+--------------+
|    users     |
+--------------+
| id (PK)      |
| email        |
| created_at   |
+--------------+
""",
        assertions={
            "required_labels": ["users", "id (PK)", "email", "created_at"],
            "forbidden_labels": [],
            "entity_count": 1,
            "required_edges": [],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Multi-section box (Task 1.9)

A single box with "users" in the top section, a horizontal divider, then three
fields: "id (PK)", "email", "created_at".

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. outer_box_closed: outer box has four + corners and proper walls
2. users_label: "users" appears in the top section
3. internal_divider: a horizontal divider line (+-...+ or |---|) separates the two sections
4. id_pk: "id (PK)" appears in the lower section
5. email: "email" appears in the lower section
6. created_at: "created_at" appears in the lower section
7. divider_aligned: internal divider connects to the side walls

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.10",
        prompt='Draw a flowchart decision diamond labeled "Is auth?" with two exit paths: a "Yes" path going right to a box labeled "Dashboard", and a "No" path going down to a box labeled "Login Page". Use / and \\ characters to form the diamond shape.',
        reference=r"""
       /---------\
      / Is auth? \
      \           /---- Yes ---->+-----------+
       \---------/                | Dashboard |
            |                     +-----------+
            | No
            v
      +------------+
      | Login Page |
      +------------+
""",
        assertions={
            "required_labels": ["Is auth?", "Yes", "No", "Dashboard", "Login Page"],
            "forbidden_labels": [],
            "entity_count": 2,
            "required_edges": [],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Decision diamond (Task 1.10)

A diamond shape (using / and \\) labeled "Is auth?", with "Yes" right to Dashboard
and "No" down to Login Page.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. diamond_chars: / and \\ characters are used to form a diamond/rhombus shape
2. question_label: "Is auth?" appears inside or adjacent to the diamond
3. yes_label: "Yes" appears near the right exit
4. no_label: "No" appears near the downward exit
5. dashboard_box: a box labeled "Dashboard" exists to the right
6. loginpage_box: a box labeled "Login Page" exists below

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.11",
        prompt='Draw a single ASCII box labeled "Config" containing two lines of content: "host: localhost" on the first line and "port: 8080" on the second line.',
        reference="""
+-------------------+
|      Config       |
| host: localhost   |
| port: 8080        |
+-------------------+
""",
        assertions={
            "required_labels": ["Config", "host: localhost", "port: 8080"],
            "forbidden_labels": [],
            "entity_count": 1,
            "required_edges": [],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Multi-line box content (Task 1.11)

Single box with "Config" at top (or as title), then "host: localhost" and "port: 8080" inside.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. box_closed: closed box with + corners
2. config_label: "Config" present
3. host_line: "host: localhost" present inside box
4. port_line: "port: 8080" present inside box

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.12",
        prompt='Draw three boxes in an L-shape: "Node A" on the top-left, "Node B" to the right of Node A, and "Node C" below Node B. Connect A to B with a right arrow, and B to C with a downward arrow.',
        reference="""
+--------+     +--------+
| Node A |---->| Node B |
+--------+     +--------+
                    |
                    v
               +--------+
               | Node C |
               +--------+
""",
        assertions={
            "required_labels": ["Node A", "Node B", "Node C"],
            "forbidden_labels": [],
            "entity_count": 3,
            "required_edges": [{"from": "Node A", "to": "Node B"}, {"from": "Node B", "to": "Node C"}],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: L-shape layout (Task 1.12)

Node A → Node B (horizontal), Node B → Node C (vertical down). Forms an L.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. node_a: "Node A" box exists
2. node_b: "Node B" box exists
3. node_c: "Node C" box exists
4. a_to_b_horizontal: arrow from A to B going right
5. b_to_c_vertical: arrow from B to C going down
6. l_shape: A and B are at the same height; C is below B (not below A)

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.13",
        prompt='Draw an ASCII box with a title bar. Use "=" as the divider between the title and content. Title: "Server Status". Content: "Running".',
        reference="""
+---------------+
| Server Status |
|===============|
|    Running    |
+---------------+
""",
        assertions={
            "required_labels": ["Server Status", "Running"],
            "forbidden_labels": [],
            "entity_count": 1,
            "required_edges": [],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Title bar box (Task 1.13)

Box with "Server Status" in the title, = divider, then "Running" below.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. box_closed: closed box
2. title_label: "Server Status" in top section
3. equals_divider: = characters used as internal divider (not - or +)
4. running_label: "Running" in content section below divider

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.14",
        prompt='Draw two boxes "Client" and "Server" side by side. Between them show two arrows: one going right labeled "request" and one going left labeled "response".',
        reference="""
          request
+--------+------->+--------+
| Client |        | Server |
+--------+<-------+--------+
          response
""",
        assertions={
            "required_labels": ["Client", "Server", "request", "response"],
            "forbidden_labels": [],
            "entity_count": 2,
            "required_edges": [{"from": "Client", "to": "Server"}, {"from": "Server", "to": "Client"}],
            "required_edge_labels": ["request", "response"],
            "preserved_elements": [],
        },
        judge="""
TASK: Labeled bidirectional arrow (Task 1.14)

Client and Server with two labeled arrows: "request" going right, "response" going left.

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. client_box: "Client" exists
2. server_box: "Server" exists
3. request_label: "request" label on rightward arrow
4. response_label: "response" label on leftward arrow
5. both_directions: arrows going both ways

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
""",
    )
    add_task(
        "1.15",
        prompt='Draw a circle node labeled "Start" using ( ) notation, connected with a right arrow to a rectangular box labeled "Process".',
        reference="""
( Start )---->+---------+
              | Process |
              +---------+
""",
        assertions={
            "required_labels": ["Start", "Process"],
            "forbidden_labels": [],
            "entity_count": 1,
            "required_edges": [{"from": "Start", "to": "Process"}],
            "required_edge_labels": [],
            "preserved_elements": [],
        },
        judge="""
TASK: Circle node and box (Task 1.15)

( Start ) connected with arrow to a box labeled "Process".

MODEL OUTPUT:
---
{model_output}
---

CHECKLIST:
1. circle_notation: ( ) or (  ) used around "Start" label (not a box)
2. start_label: "Start" present
3. process_box: a closed rectangular box labeled "Process" exists
4. arrow_connecting: arrow from Start to Process

RESPOND: {"scores": {...}, "total": 0, "pass": false, "reason": "string"}
        """,
    )
    c2_common = {
        "forbidden_labels": [],
        "required_edge_labels": [],
        "preserved_elements": [],
    }
    add_task("2.1", prompt='Draw a client-server-database chain: "Browser" → "Web Server" → "PostgreSQL". Show arrows between each.',
             reference="""
+-----------+    +------------+    +------------+
|  Browser  |--->| Web Server |--->| PostgreSQL |
+-----------+    +------------+    +------------+
""",
             assertions={**c2_common, "required_labels": ["Browser", "Web Server", "PostgreSQL"], "entity_count": 3,
                         "required_edges": [{"from": "Browser", "to": "Web Server"}, {"from": "Web Server", "to": "PostgreSQL"}]},
             judge="TASK: Client-server-database chain (Task 2.1)\n\nCHECKLIST: browser_box, webserver_box, postgres_box, browser_to_server_arrow, server_to_db_arrow.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.2", prompt='Draw a load balancer "NGINX" receiving traffic from "Client" and distributing to three backends: "App-1", "App-2", "App-3".',
             reference="""
            +---------+
            |  NGINX  |
            +---------+
            ^    |    ^
            |    |    |
       +--------+ | +--------+
       | Client | | | App-3  |
       +--------+ | +--------+
                 v
      +--------+   +--------+
      | App-1  |   | App-2  |
      +--------+   +--------+
""",
             assertions={**c2_common, "required_labels": ["Client", "NGINX", "App-1", "App-2", "App-3"], "entity_count": 5,
                         "required_edges": [{"from": "Client", "to": "NGINX"}, {"from": "NGINX", "to": "App-1"}, {"from": "NGINX", "to": "App-2"}, {"from": "NGINX", "to": "App-3"}]},
             judge="TASK: NGINX load balancer (Task 2.2)\n\nCHECKLIST: client_box, nginx_box, three_app_boxes, client_to_nginx, nginx_to_all_three.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.3", prompt='Draw a Raft consensus cluster with 5 nodes. One is labeled "Leader". The others are "Follower-1", "Follower-2", "Follower-3", "Follower-4". Show heartbeat arrows from Leader to each Follower only (not the reverse).',
             reference="""
                 +--------+
                 | Leader |
                 +--------+
                  /  |  \\
                 v   v   v
      +------------+ +------------+ +------------+
      | Follower-1 | | Follower-2 | | Follower-3 |
      +------------+ +------------+ +------------+
                        |
                        v
                   +------------+
                   | Follower-4 |
                   +------------+
""",
             assertions={**c2_common, "required_labels": ["Leader", "Follower-1", "Follower-2", "Follower-3", "Follower-4"], "entity_count": 5,
                         "required_edges": [{"from": "Leader", "to": "Follower-1"}, {"from": "Leader", "to": "Follower-2"}, {"from": "Leader", "to": "Follower-3"}, {"from": "Leader", "to": "Follower-4"}]},
             judge="TASK: Raft cluster (Task 2.3)\n\nCHECKLIST: leader_box, four_follower_boxes, four_heartbeat_arrows, direction_leader_to_followers_not_reverse, no_follower_to_follower_edges.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.4", prompt='Draw a ring network with 4 nodes: "Node-A", "Node-B", "Node-C", "Node-D". Connect them in a ring: A→B→C→D→A.',
             reference="""
+--------+ ----> +--------+
| Node-A |       | Node-B |
+--------+ <---- +--------+
    ^                |
    |                v
+--------+ <---- +--------+
| Node-D |       | Node-C |
+--------+ ----> +--------+
""",
             assertions={**c2_common, "required_labels": ["Node-A", "Node-B", "Node-C", "Node-D"], "entity_count": 4,
                         "required_edges": [{"from": "Node-A", "to": "Node-B"}, {"from": "Node-B", "to": "Node-C"}, {"from": "Node-C", "to": "Node-D"}, {"from": "Node-D", "to": "Node-A"}]},
             judge="TASK: Ring network (Task 2.4)\n\nCHECKLIST: four_nodes, a_to_b, b_to_c, c_to_d, d_to_a_ring_closure.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.5", prompt='Draw a Kubernetes cluster. One outer box labeled "Control Plane" contains three sub-components: "API Server", "etcd", "Scheduler". Below the Control Plane, three worker boxes: "Worker-1", "Worker-2", "Worker-3". Connect Control Plane to each Worker.',
             reference="""
+--------------------------------------+
|            Control Plane             |
|  +------------+ +------+ +---------+ |
|  | API Server | | etcd | |Scheduler| |
|  +------------+ +------+ +---------+ |
+--------------------------------------+
         |              |              |
         v              v              v
   +----------+   +----------+   +----------+
   | Worker-1 |   | Worker-2 |   | Worker-3 |
   +----------+   +----------+   +----------+
""",
             assertions={**c2_common, "required_labels": ["Control Plane", "API Server", "etcd", "Scheduler", "Worker-1", "Worker-2", "Worker-3"], "entity_count": 4,
                         "required_edges": [{"from": "Control Plane", "to": "Worker-1"}, {"from": "Control Plane", "to": "Worker-2"}, {"from": "Control Plane", "to": "Worker-3"}]},
             judge="TASK: Kubernetes cluster (Task 2.5)\n\nCHECKLIST: control_plane_outer_box, api_server_inside_cp, etcd_inside_cp, scheduler_inside_cp, three_workers_below, cp_to_all_workers.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.6", prompt='Draw a pub/sub diagram. "Order Service" publishes to "Kafka". "Inventory Service" and "Notification Service" both subscribe from Kafka. Label the arrow from Order Service to Kafka "publish". Label arrows from Kafka to subscribers "subscribe".',
             reference="""
 Order Service
+---------------+
| Order Service |
+---------------+
     | publish
     v
+-------+
| Kafka |
+-------+
  | subscribe        | subscribe
  v                  v
+-------------------+  +----------------------+
| Inventory Service |  | Notification Service |
+-------------------+  +----------------------+
""",
             assertions={**c2_common, "required_labels": ["Order Service", "Kafka", "Inventory Service", "Notification Service", "publish", "subscribe"], "entity_count": 4,
                         "required_edges": [{"from": "Order Service", "to": "Kafka"}, {"from": "Kafka", "to": "Inventory Service"}, {"from": "Kafka", "to": "Notification Service"}],
                         "required_edge_labels": ["publish", "subscribe"]},
             judge="TASK: Pub/sub (Task 2.6)\n\nCHECKLIST: order_service, kafka, inventory_service, notification_service, publish_label, subscribe_labels, correct_directions.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.7", prompt='Draw a home ML lab cluster. One "Mac Mini M4 (Orchestrator)" at the top connected via "Thunderbolt" to three workers: "Mac Mini M4 Worker-1", "Mac Mini M4 Worker-2", "Mac Mini M4 Worker-3". Also show a "NAS" box connected only to the Orchestrator.',
             reference="""
                        +-----------------------------+
                        | Mac Mini M4 (Orchestrator) |
                        +-----------------------------+
             Thunderbolt /      |       \ Thunderbolt
                       v         v        v
 +------------------------+ +------------------------+ +------------------------+
 | Mac Mini M4 Worker-1   | | Mac Mini M4 Worker-2   | | Mac Mini M4 Worker-3   |
 +------------------------+ +------------------------+ +------------------------+
             ^
             |
        +--------+
        |  NAS   |
        +--------+
""",
             assertions={"required_labels": ["Mac Mini M4 (Orchestrator)", "Mac Mini M4 Worker-1", "Mac Mini M4 Worker-2", "Mac Mini M4 Worker-3", "NAS", "Thunderbolt"],
                         "forbidden_labels": [], "entity_count": 5,
                         "required_edges": [{"from": "Orchestrator", "to": "Worker-1"}, {"from": "Orchestrator", "to": "Worker-2"}, {"from": "Orchestrator", "to": "Worker-3"}, {"from": "NAS", "to": "Orchestrator"}],
                         "required_edge_labels": ["Thunderbolt"], "preserved_elements": []},
             judge="TASK: Home ML lab cluster (Task 2.7)\n\nCHECKLIST: orchestrator, three_workers, nas_box, thunderbolt_label, nas_to_orchestrator_only_not_workers.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.8", prompt='Draw a diagram with "Mac Mini M4 (Training)" at the top connected via "SSH / TCP" to four inference nodes in a row: "Jetson Orin Nano-1", "Jetson Orin Nano-2", "Jetson Orin Nano-3", "Jetson Orin Nano-4".',
             reference="""
                   +-------------------------+
                   | Mac Mini M4 (Training) |
                   +-------------------------+
                      SSH / TCP to all nodes
               /          |          |          \\
              v           v          v           v
+--------------------+ +--------------------+ +--------------------+ +--------------------+
| Jetson Orin Nano-1 | | Jetson Orin Nano-2 | | Jetson Orin Nano-3 | | Jetson Orin Nano-4 |
+--------------------+ +--------------------+ +--------------------+ +--------------------+
""",
             assertions={"required_labels": ["Mac Mini M4 (Training)", "Jetson Orin Nano-1", "Jetson Orin Nano-2", "Jetson Orin Nano-3", "Jetson Orin Nano-4", "SSH / TCP"],
                         "forbidden_labels": [], "entity_count": 5,
                         "required_edges": [{"from": "Mac Mini", "to": "Jetson-1"}, {"from": "Mac Mini", "to": "Jetson-2"}, {"from": "Mac Mini", "to": "Jetson-3"}, {"from": "Mac Mini", "to": "Jetson-4"}],
                         "required_edge_labels": ["SSH / TCP"], "preserved_elements": []},
             judge="TASK: Training to inference nodes (Task 2.8)\n\nCHECKLIST: mac_mini_top, four_jetsons_in_row, ssh_tcp_label, four_connections.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.9", prompt='Draw a BitTorrent swarm. One "Tracker" connects to 5 peers: "Peer-A", "Peer-B", "Peer-C", "Peer-D", "Peer-E". Additionally show peer-to-peer connections: A-B, B-C, C-D, D-E, and A-E.',
             reference="""
                           +---------+
                           | Tracker |
                           +---------+
                         /  |  |  |   \\
                        v   v  v  v    v
 +--------+<-------->+--------+<-------->+--------+<-------->+--------+
 | Peer-A |          | Peer-B |          | Peer-C |          | Peer-D |
 +--------+          +--------+          +--------+          +--------+
     ^                                                        |
     |                                                        v
     +----------------------------<-------->+--------+<------+
                                            | Peer-E |
                                            +--------+
""",
             assertions={"required_labels": ["Tracker", "Peer-A", "Peer-B", "Peer-C", "Peer-D", "Peer-E"], "forbidden_labels": [], "entity_count": 6,
                         "required_edges": [{"from": "Tracker", "to": "Peer-A"}, {"from": "Tracker", "to": "Peer-B"}, {"from": "Tracker", "to": "Peer-C"}, {"from": "Tracker", "to": "Peer-D"}, {"from": "Tracker", "to": "Peer-E"},
                                            {"from": "Peer-A", "to": "Peer-B"}, {"from": "Peer-B", "to": "Peer-C"}, {"from": "Peer-C", "to": "Peer-D"}, {"from": "Peer-D", "to": "Peer-E"}, {"from": "Peer-A", "to": "Peer-E"}],
                         "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: BitTorrent swarm (Task 2.9)\n\nCHECKLIST: tracker, five_peers, tracker_to_all_five, p2p_ab, p2p_bc, p2p_cd, p2p_de, p2p_ae.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.10", prompt='Draw a DiLoCo training diagram. Four "Worker" boxes in a row, each connected downward to a local "Inner Optimizer" box. One "Outer Optimizer" box above all workers, connected to each worker with dashed arrows (- - >). Label the dashed arrows "outer loop sync".',
             reference="""
                           +-----------------+
                           | Outer Optimizer |
                           +-----------------+
                 outer loop sync - - > to all workers
        - - >          - - >          - - >          - - >
+--------+      +--------+      +--------+      +--------+
|Worker-1|      |Worker-2|      |Worker-3|      |Worker-4|
+--------+      +--------+      +--------+      +--------+
    |               |               |               |
    v               v               v               v
+---------------++---------------++---------------++---------------+
|Inner Optimizer||Inner Optimizer||Inner Optimizer||Inner Optimizer|
+---------------++---------------++---------------++---------------+
""",
             assertions={"required_labels": ["Worker", "Inner Optimizer", "Outer Optimizer", "outer loop sync"], "forbidden_labels": [], "entity_count": 9, "required_edges": [], "required_edge_labels": ["outer loop sync"], "preserved_elements": []},
             judge="TASK: DiLoCo training (Task 2.10)\n\nCHECKLIST: four_workers, four_inner_optimizers, outer_optimizer, dashed_arrows_outer_to_workers, outer_loop_sync_label.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.11", prompt='Draw a ring allreduce topology. Four GPU nodes in a directed ring: "GPU-0" → "GPU-1" → "GPU-2" → "GPU-3" → "GPU-0". All arrows go clockwise. Label each arrow "gradient".',
             reference="""
          gradient                gradient
+-------+ --------> +-------+ --------> +-------+
| GPU-0 |           | GPU-1 |           | GPU-2 |
+-------+ <-------- +-------+ <-------- +-------+
    ^                   gradient             |
    |                                        | gradient
    +--------------------- +-------+ <-------+
                          | GPU-3 |
                          +-------+
""",
             assertions={"required_labels": ["GPU-0", "GPU-1", "GPU-2", "GPU-3", "gradient"], "forbidden_labels": [], "entity_count": 4,
                         "required_edges": [{"from": "GPU-0", "to": "GPU-1"}, {"from": "GPU-1", "to": "GPU-2"}, {"from": "GPU-2", "to": "GPU-3"}, {"from": "GPU-3", "to": "GPU-0"}],
                         "required_edge_labels": ["gradient"], "preserved_elements": []},
             judge="TASK: Ring allreduce (Task 2.11)\n\nCHECKLIST: four_gpus, directed_ring_0_1_2_3_0, ring_closure_3_to_0, gradient_labels, all_same_direction.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.12", prompt='Draw a peer discovery diagram. Six Pi nodes in two rows of three: top row "Pi-1", "Pi-2", "Pi-3"; bottom row "Pi-4", "Pi-5", "Pi-6". Show dotted broadcast lines (using ...) between all Pi nodes representing mDNS multicast. One "Tracker" node to the side connected only to Pi-1.',
             reference="""
+------+ ... +------+ ... +------+
| Pi-1 | ... | Pi-2 | ... | Pi-3 |
+------+ ... +------+ ... +------+
   |                    ...   |
   |                          |
+------+ ... +------+ ... +------+
| Pi-4 | ... | Pi-5 | ... | Pi-6 |
+------+ ... +------+ ... +------+
   ^
   |
+---------+
| Tracker |
+---------+
""",
             assertions={"required_labels": ["Pi-1", "Pi-2", "Pi-3", "Pi-4", "Pi-5", "Pi-6", "Tracker"], "forbidden_labels": [], "entity_count": 7, "required_edges": [], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Peer discovery (Task 2.12)\n\nCHECKLIST: six_pi_nodes_two_rows, tracker_exists, broadcast_indication_dotted_lines, tracker_to_pi1_only.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.13", prompt='Draw a parameter server architecture. One "Parameter Server" at the top. Four "Worker" boxes below it. Show bidirectional arrows between PS and each worker labeled "push gradients" (Worker→PS) and "pull params" (PS→Worker).',
             reference="""
                         +------------------+
                         | Parameter Server |
                         +------------------+
                    pull params to all workers
               /             |             |             \\
              v              v             v              v
+--------+  <---- push gradients ----> +--------+  +--------+  +--------+
|Worker-1|                             |Worker-2|  |Worker-3|  |Worker-4|
+--------+                             +--------+  +--------+  +--------+
""",
             assertions={"required_labels": ["Parameter Server", "Worker", "push gradients", "pull params"], "forbidden_labels": [], "entity_count": 5, "required_edges": [], "required_edge_labels": ["push gradients", "pull params"], "preserved_elements": []},
             judge="TASK: Parameter server (Task 2.13)\n\nCHECKLIST: parameter_server, four_workers, push_gradients_labels, pull_params_labels, bidirectional_ps_worker_links.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.14", prompt='Draw a primary-replica database setup. One "Primary DB" on the left. Three replicas to the right: "Replica-1", "Replica-2", "Replica-3". Show arrows from Primary to each Replica labeled "async sync".',
             reference="""
+------------+    async sync    +-----------+
| Primary DB |----------------->| Replica-1 |
+------------+                  +-----------+
      | async sync                   +-----------+
      +----------------------------->| Replica-2 |
      |                              +-----------+
      | async sync                   +-----------+
      +----------------------------->| Replica-3 |
                                     +-----------+
""",
             assertions={"required_labels": ["Primary DB", "Replica-1", "Replica-2", "Replica-3", "async sync"], "forbidden_labels": [], "entity_count": 4,
                         "required_edges": [{"from": "Primary DB", "to": "Replica-1"}, {"from": "Primary DB", "to": "Replica-2"}, {"from": "Primary DB", "to": "Replica-3"}],
                         "required_edge_labels": ["async sync"], "preserved_elements": []},
             judge="TASK: Primary-replica DB (Task 2.14)\n\nCHECKLIST: primary_db, three_replicas, primary_to_all_replicas, async_sync_labels.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.15", prompt='Draw a service mesh with sidecars. Three services in a row: "Service A", "Service B", "Service C". Each has a small sidecar box directly below it labeled "Proxy". All Proxy boxes connect to a central "Control Plane" box below.',
             reference="""
+-----------+   +-----------+   +-----------+
| Service A |   | Service B |   | Service C |
+-----------+   +-----------+   +-----------+
      |               |               |
      v               v               v
+-------+         +-------+       +-------+
| Proxy |         | Proxy |       | Proxy |
+-------+         +-------+       +-------+
      \               |               /
       \              |              /
        v             v             v
           +---------------+
           | Control Plane |
           +---------------+
""",
             assertions={"required_labels": ["Service A", "Service B", "Service C", "Proxy", "Control Plane"], "forbidden_labels": [], "entity_count": 7, "required_edges": [], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Service mesh with sidecars (Task 2.15)\n\nCHECKLIST: three_services, three_proxies, proxy_under_each_service, proxies_to_control_plane.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.16", prompt='Draw a CDN architecture. One "Origin Server" on the right. Two edge cache nodes: "Edge-US" and "Edge-EU". "Users (Global)" on the left connecting to both edge nodes. Edge nodes connect to Origin on cache miss. Label edge-to-origin arrows "cache miss".',
             reference="""
+----------------+   +---------+   +---------------+
| Users (Global) |-->| Edge-US |-->| Origin Server |
+----------------+   +---------+   +---------------+
        |               cache miss^
        |                          |
        +--------->+---------+-----+
                   | Edge-EU |
                   +---------+
""",
             assertions={"required_labels": ["Users (Global)", "Edge-US", "Edge-EU", "Origin Server", "cache miss"], "forbidden_labels": [], "entity_count": 4,
                         "required_edges": [{"from": "Users (Global)", "to": "Edge-US"}, {"from": "Users (Global)", "to": "Edge-EU"}, {"from": "Edge-US", "to": "Origin Server"}, {"from": "Edge-EU", "to": "Origin Server"}],
                         "required_edge_labels": ["cache miss"], "preserved_elements": []},
             judge="TASK: CDN architecture (Task 2.16)\n\nCHECKLIST: users, two_edges, origin, users_to_both_edges, both_edges_to_origin, cache_miss_labels.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.17", prompt='Draw a Raspberry Pi PoE cluster. "Internet" at top connects to "Router". Router connects to "TP-Link Switch". Switch connects to four Pi nodes: "Pi-1", "Pi-2", "Pi-3", "Pi-4".',
             reference="""
+----------+
| Internet |
+----------+
     |
     v
+--------+
| Router |
+--------+
     |
     v
+----------------+
| TP-Link Switch |
+----------------+
  |      |      |      |
  v      v      v      v
+------+ +------+ +------+ +------+
| Pi-1 | | Pi-2 | | Pi-3 | | Pi-4 |
+------+ +------+ +------+ +------+
""",
             assertions={"required_labels": ["Internet", "Router", "TP-Link Switch", "Pi-1", "Pi-2", "Pi-3", "Pi-4"], "forbidden_labels": [], "entity_count": 7,
                         "required_edges": [{"from": "Internet", "to": "Router"}, {"from": "Router", "to": "TP-Link Switch"}, {"from": "TP-Link Switch", "to": "Pi-1"}, {"from": "TP-Link Switch", "to": "Pi-2"}, {"from": "TP-Link Switch", "to": "Pi-3"}, {"from": "TP-Link Switch", "to": "Pi-4"}],
                         "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Pi PoE cluster (Task 2.17)\n\nCHECKLIST: internet, router, switch, four_pis, correct_tree_connections.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.18", prompt='Draw a VPN tunnel. "Client" on the left connects through an "[Encrypted Tunnel]" annotation to "VPN Server" in the middle. VPN Server connects to "Internet" on the right.',
             reference="""
+--------+   [Encrypted Tunnel]   +------------+   +----------+
| Client |----------------------->| VPN Server |-->| Internet |
+--------+                        +------------+   +----------+
""",
             assertions={"required_labels": ["Client", "VPN Server", "Internet", "[Encrypted Tunnel]"], "forbidden_labels": [], "entity_count": 3,
                         "required_edges": [{"from": "Client", "to": "VPN Server"}, {"from": "VPN Server", "to": "Internet"}],
                         "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: VPN tunnel (Task 2.18)\n\nCHECKLIST: client, encrypted_tunnel_annotation, vpn_server, internet, two_step_flow.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.19", prompt='Draw DNS resolution. "Browser" → "Local Resolver" → "Root NS" → "TLD NS (.com)" → "Auth NS (example.com)" → "IP Address returned". Linear chain left to right.',
             reference="""
+---------+ -> +----------------+ -> +---------+ -> +---------------+ -> +-----------------------+ -> +---------------------+
| Browser |    | Local Resolver |    | Root NS |    | TLD NS (.com) |    | Auth NS (example.com) |    | IP Address returned |
+---------+    +----------------+    +---------+    +---------------+    +-----------------------+    +---------------------+
""",
             assertions={"required_labels": ["Browser", "Local Resolver", "Root NS", "TLD NS (.com)", "Auth NS (example.com)", "IP Address returned"], "forbidden_labels": [], "entity_count": 6,
                         "required_edges": [{"from": "Browser", "to": "Local Resolver"}, {"from": "Local Resolver", "to": "Root NS"}, {"from": "Root NS", "to": "TLD NS (.com)"}, {"from": "TLD NS (.com)", "to": "Auth NS (example.com)"}, {"from": "Auth NS (example.com)", "to": "IP Address returned"}],
                         "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: DNS resolution (Task 2.19)\n\nCHECKLIST: all_six_nodes, linear_chain, correct_left_to_right_order.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.20", prompt='Draw a TCP three-way handshake between "Client" and "Server" using a sequence diagram (vertical lanes). Show: Client sends SYN →, Server replies ← SYN-ACK, Client sends ACK →.',
             reference="""
Client                      Server
  |                           |
  |-------- SYN ------------->|
  |<----- SYN-ACK ------------|
  |-------- ACK ------------->|
  |                           |
""",
             assertions={"required_labels": ["Client", "Server", "SYN", "SYN-ACK", "ACK"], "forbidden_labels": [], "entity_count": 0, "required_edges": [], "required_edge_labels": ["SYN", "SYN-ACK", "ACK"], "preserved_elements": []},
             judge="TASK: TCP three-way handshake (Task 2.20)\n\nCHECKLIST: client_lane, server_lane, syn_right, synack_left, ack_right.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.21", prompt='Draw an event-driven system. Three producers: "Service A", "Service B", "Service C". All publish to "Event Bus". Two consumers subscribe from Event Bus: "Analytics Service", "Audit Service".',
             reference="""
+-----------+  +-----------+  +-----------+
| Service A |  | Service B |  | Service C |
+-----------+  +-----------+  +-----------+
      \             |             /
       \            |            /
        v           v           v
             +-----------+
             | Event Bus |
             +-----------+
               |       |
               v       v
     +-------------------+  +---------------+
     | Analytics Service |  | Audit Service |
     +-------------------+  +---------------+
""",
             assertions={"required_labels": ["Service A", "Service B", "Service C", "Event Bus", "Analytics Service", "Audit Service"], "forbidden_labels": [], "entity_count": 6,
                         "required_edges": [{"from": "Service A", "to": "Event Bus"}, {"from": "Service B", "to": "Event Bus"}, {"from": "Service C", "to": "Event Bus"}, {"from": "Event Bus", "to": "Analytics Service"}, {"from": "Event Bus", "to": "Audit Service"}],
                         "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Event-driven system (Task 2.21)\n\nCHECKLIST: three_producers, event_bus, two_consumers, producers_to_bus, bus_to_consumers.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.22", prompt='Draw a federated learning setup. One "Central Aggregator" in the middle. Four local trainers around it: "Trainer-1", "Trainer-2", "Trainer-3", "Trainer-4". Bidirectional arrows between Aggregator and each Trainer labeled "model update".',
             reference="""
             +--------------------+
             | Central Aggregator |
             +--------------------+
          <-->    <-->    <-->    <-->
      +-----------+ +-----------+ +-----------+ +-----------+
      | Trainer-1 | | Trainer-2 | | Trainer-3 | | Trainer-4 |
      +-----------+ +-----------+ +-----------+ +-----------+
                 model update on each link
""",
             assertions={"required_labels": ["Central Aggregator", "Trainer-1", "Trainer-2", "Trainer-3", "Trainer-4", "model update"], "forbidden_labels": [], "entity_count": 5, "required_edges": [], "required_edge_labels": ["model update"], "preserved_elements": []},
             judge="TASK: Federated learning (Task 2.22)\n\nCHECKLIST: aggregator, four_trainers, bidirectional_links, model_update_labels.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.23", prompt='Draw speculative decoding. "Draft Model (small)" generates tokens passed to "Verifier Model (large)". Show two output paths: "accept" going to "Output" and "reject" looping back to Draft Model.',
             reference="""
+---------------------+ ---> +------------------------+
| Draft Model (small) |      | Verifier Model (large) |
+---------------------+      +------------------------+
          ^                         |            \\
          | reject                  | accept      \\
          +-------------------------+              v
                                           +--------+
                                           | Output |
                                           +--------+
""",
             assertions={"required_labels": ["Draft Model (small)", "Verifier Model (large)", "Output", "accept", "reject"], "forbidden_labels": [], "entity_count": 3,
                         "required_edges": [{"from": "Draft Model (small)", "to": "Verifier Model (large)"}, {"from": "Verifier Model (large)", "to": "Output"}, {"from": "Verifier Model (large)", "to": "Draft Model (small)"}],
                         "required_edge_labels": ["accept", "reject"], "preserved_elements": []},
             judge="TASK: Speculative decoding (Task 2.23)\n\nCHECKLIST: draft_model, verifier_model, output, accept_path, reject_loopback.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.24", prompt='Draw PagedAttention KV cache. Show "Logical Blocks" on the left (Block 0, Block 1, Block 2) mapped via arrows to "Physical Blocks" on the right (Physical 3, Physical 0, Physical 7). Add a "Block Table" box in the middle showing the mapping.',
             reference="""
+--------------+     +-------------------+     +----------------+
| Logical Block | --> | Block Table       | --> | Physical 3     |
| Block 0       |     | 0 -> 3            |     +----------------+
| Block 1       | --> | 1 -> 0            | --> +----------------+
| Block 2       |     | 2 -> 7            |     | Physical 0     |
+--------------+     +-------------------+     +----------------+
                                                +----------------+
                                                | Physical 7     |
                                                +----------------+
""",
             assertions={"required_labels": ["Logical Blocks", "Block 0", "Block 1", "Block 2", "Physical 3", "Physical 0", "Physical 7", "Block Table"], "forbidden_labels": [], "entity_count": 5, "required_edges": [], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: PagedAttention KV cache (Task 2.24)\n\nCHECKLIST: logical_blocks, block_table, three_physical_blocks, mapping_indicated.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.25", prompt='Draw FSDP sharding. Four GPU boxes: "GPU-0 (Shard 0)", "GPU-1 (Shard 1)", "GPU-2 (Shard 2)", "GPU-3 (Shard 3)". Show AllGather arrows between all GPUs (each to each) labeled "allgather".',
             reference="""
+-----------------+<-------->+-----------------+
| GPU-0 (Shard 0) | allgather | GPU-1 (Shard 1) |
+-----------------+<-------->+-----------------+
        ^   \                    /   ^
        |    \ allgather  allgather  |
        |     \                /     |
+-----------------+<-------->+-----------------+
| GPU-2 (Shard 2) | allgather | GPU-3 (Shard 3) |
+-----------------+<-------->+-----------------+
""",
             assertions={"required_labels": ["GPU-0 (Shard 0)", "GPU-1 (Shard 1)", "GPU-2 (Shard 2)", "GPU-3 (Shard 3)", "allgather"], "forbidden_labels": [], "entity_count": 4, "required_edges": [], "required_edge_labels": ["allgather"], "preserved_elements": []},
             judge="TASK: FSDP sharding (Task 2.25)\n\nCHECKLIST: four_gpu_shards, allgather_labels, dense_all_to_all_connectivity_indicated.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.26", prompt='Draw a CI/CD pipeline as a left-to-right chain: "Code Push" → "Build" → "Unit Tests" → "Integration Tests" → "Staging" → "Production".',
             reference="""
+-----------+ -> +-------+ -> +------------+ -> +-------------------+ -> +---------+ -> +------------+
| Code Push |    | Build |    | Unit Tests |    | Integration Tests |    | Staging |    | Production |
+-----------+    +-------+    +------------+    +-------------------+    +---------+    +------------+
""",
             assertions={"required_labels": ["Code Push", "Build", "Unit Tests", "Integration Tests", "Staging", "Production"], "forbidden_labels": [], "entity_count": 6,
                         "required_edges": [{"from": "Code Push", "to": "Build"}, {"from": "Build", "to": "Unit Tests"}, {"from": "Unit Tests", "to": "Integration Tests"}, {"from": "Integration Tests", "to": "Staging"}, {"from": "Staging", "to": "Production"}],
                         "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: CI/CD chain (Task 2.26)\n\nCHECKLIST: six_stages, correct_order, adjacent_arrows.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.27", prompt='Draw an API gateway pattern. "Client" connects to "API Gateway". Inside the gateway show "Auth" and "Rate Limiter" as sub-components. Gateway routes to three services: "User Service", "Order Service", "Product Service".',
             reference="""
+--------+    +------------------------------+
| Client |--->|         API Gateway          |
+--------+    | +------+   +--------------+  |
              | | Auth |   | Rate Limiter |  |
              | +------+   +--------------+  |
              +------------------------------+
                 |            |            |
                 v            v            v
         +--------------+ +---------------+ +-----------------+
         | User Service | | Order Service | | Product Service |
         +--------------+ +---------------+ +-----------------+
""",
             assertions={"required_labels": ["Client", "API Gateway", "Auth", "Rate Limiter", "User Service", "Order Service", "Product Service"], "forbidden_labels": [], "entity_count": 5,
                         "required_edges": [{"from": "Client", "to": "API Gateway"}, {"from": "API Gateway", "to": "User Service"}, {"from": "API Gateway", "to": "Order Service"}, {"from": "API Gateway", "to": "Product Service"}],
                         "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: API gateway pattern (Task 2.27)\n\nCHECKLIST: client, gateway, auth_inside, rate_limiter_inside, gateway_to_three_services.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.28", prompt='Draw a Kubernetes sidecar pattern. One "Pod" box containing two sub-boxes side by side: "App Container" and "Proxy Sidecar". The proxy connects to "Service Mesh" outside the pod.',
             reference="""
+-------------------------------------+
|                 Pod                 |
|  +---------------+ +--------------+ |
|  | App Container | | Proxy Sidecar| |
|  +---------------+ +--------------+ |
+-------------------------------------+
                         |
                         v
                  +--------------+
                  | Service Mesh |
                  +--------------+
""",
             assertions={"required_labels": ["Pod", "App Container", "Proxy Sidecar", "Service Mesh"], "forbidden_labels": [], "entity_count": 2,
                         "required_edges": [{"from": "Proxy Sidecar", "to": "Service Mesh"}], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Kubernetes sidecar pattern (Task 2.28)\n\nCHECKLIST: pod_outer_box, app_container_inside, proxy_sidecar_inside, proxy_to_service_mesh.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.29", prompt='Draw a 3-node Paxos cluster. Show "Proposer" sending "Prepare(n)" to three "Acceptor" boxes. Acceptors reply "Promise(n)" back to Proposer. Then Proposer sends "Accept(n,v)" to Acceptors.',
             reference="""
                     +----------+
                     | Proposer |
                     +----------+
         Prepare(n) /    |    \ Prepare(n)
                  v      v      v
            +----------+ +----------+ +----------+
            |Acceptor-1| |Acceptor-2| |Acceptor-3|
            +----------+ +----------+ +----------+
         Promise(n) \     |     / Promise(n)
                     \    |    /
                      v   v   v
                 Accept(n,v) to all
""",
             assertions={"required_labels": ["Proposer", "Prepare(n)", "Promise(n)", "Accept(n,v)", "Acceptor"], "forbidden_labels": [], "entity_count": 4, "required_edges": [], "required_edge_labels": ["Prepare(n)", "Promise(n)", "Accept(n,v)"], "preserved_elements": []},
             judge="TASK: Paxos cluster (Task 2.29)\n\nCHECKLIST: proposer, three_acceptors, prepare_phase, promise_phase, accept_phase.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("2.30", prompt='Draw a full smolhive topology. One "Mac Mini M4 (Trainer)" at the top. Below it, four "Jetson Orin Nano" boxes and two "Raspberry Pi" boxes. Trainer connects to all six. Jetsons and Pis connect to each other with dashed "P2P sync" arrows.',
             reference="""
                   +-----------------------+
                   | Mac Mini M4 (Trainer) |
                   +-----------------------+
                 /  |   |   |   |   |   \\
                v   v   v   v   v   v    v
+-------------------+ +-------------------+ +-------------------+ +-------------------+
| Jetson Orin Nano1 | | Jetson Orin Nano2 | | Jetson Orin Nano3 | | Jetson Orin Nano4 |
+-------------------+ +-------------------+ +-------------------+ +-------------------+
         - - - - - - P2P sync - - - - - -
             +----------------+       +----------------+
             | Raspberry Pi-1 | - - - | Raspberry Pi-2 |
             +----------------+ P2P    +----------------+
""",
             assertions={"required_labels": ["Mac Mini M4 (Trainer)", "Jetson Orin Nano", "Raspberry Pi", "P2P sync"], "forbidden_labels": [], "entity_count": 7, "required_edges": [], "required_edge_labels": ["P2P sync"], "preserved_elements": []},
             judge="TASK: Smolhive topology (Task 2.30)\n\nCHECKLIST: trainer, four_jetsons, two_pis, trainer_to_all_six, dashed_p2p_sync_links.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.1", prompt='Add a "Database" box to the right of the Server box. Connect Server to Database with a right-pointing arrow. Do not change anything else.',
             source="""
+----------+     +----------+
|  Client  |---->|  Server  |
+----------+     +----------+
""",
             reference="""
+----------+     +----------+     +------------+
|  Client  |---->|  Server  |---->|  Database  |
+----------+     +----------+     +------------+
""",
             assertions={"required_labels": ["Client", "Server", "Database"], "forbidden_labels": [], "entity_count": 3, "required_edges": [{"from": "Client", "to": "Server"}, {"from": "Server", "to": "Database"}], "required_edge_labels": [], "preserved_elements": ["Client", "Server"]},
             judge="TASK: Add a node (Task 3.1)\n\nCHECKLIST: client_unchanged, server_unchanged, original_arrow_preserved, database_added, server_to_database, no_extra_changes.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.2", prompt='Remove the Cache box and its connections. Connect Web directly to DB with an arrow.',
             source="""
+-------+     +-------+     +------+
|  Web  |---->| Cache |---->|  DB  |
+-------+     +-------+     +------+
""",
             reference="""
+-------+     +------+
|  Web  |---->|  DB  |
+-------+     +------+
""",
             assertions={"required_labels": ["Web", "DB"], "forbidden_labels": ["Cache"], "entity_count": 2, "required_edges": [{"from": "Web", "to": "DB"}], "required_edge_labels": [], "preserved_elements": ["Web", "DB"]},
             judge="TASK: Remove a node (Task 3.2)\n\nCHECKLIST: cache_absent, web_present, db_present, direct_web_to_db, only_two_boxes.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.3", prompt='Rename "App Srv" to "FastAPI". Resize the box to fit the new label. Keep everything else exactly the same.',
             source="""
+--------+     +---------+
|  Nginx |---->| App Srv |
+--------+     +---------+
""",
             reference="""
+--------+     +---------+
|  Nginx |---->| FastAPI |
+--------+     +---------+
""",
             assertions={"required_labels": ["Nginx", "FastAPI"], "forbidden_labels": ["App Srv"], "entity_count": 2, "required_edges": [{"from": "Nginx", "to": "FastAPI"}], "required_edge_labels": [], "preserved_elements": ["Nginx"]},
             judge="TASK: Rename a node (Task 3.3)\n\nCHECKLIST: nginx_unchanged, app_srv_absent, fastapi_present, arrow_preserved, box_fits_label.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.4", prompt='Add a bidirectional arrow between Service and Monitor labeled "metrics" above the arrow line.',
             source="""
+---------+          +---------+
| Service |          | Monitor |
+---------+          +---------+
""",
             reference="""
             metrics
+---------+<------->+---------+
| Service |         | Monitor |
+---------+         +---------+
""",
             assertions={"required_labels": ["Service", "Monitor", "metrics"], "forbidden_labels": [], "entity_count": 2, "required_edges": [{"from": "Service", "to": "Monitor"}, {"from": "Monitor", "to": "Service"}], "required_edge_labels": ["metrics"], "preserved_elements": ["Service", "Monitor"]},
             judge="TASK: Add an edge (Task 3.4)\n\nCHECKLIST: service_unchanged, monitor_unchanged, bidirectional_connector, metrics_label.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.5", prompt='Add an internal section below the title. Use a horizontal divider (+-...+) to separate. Add two endpoints below the divider: "/login" and "/refresh".',
             source="""
+------------------+
|   Auth Service   |
+------------------+
""",
             reference="""
+------------------+
|   Auth Service   |
+------------------+
| /login           |
| /refresh         |
+------------------+
""",
             assertions={"required_labels": ["Auth Service", "/login", "/refresh"], "forbidden_labels": [], "entity_count": 1, "required_edges": [], "required_edge_labels": [], "preserved_elements": ["Auth Service"]},
             judge="TASK: Add internal section (Task 3.5)\n\nCHECKLIST: auth_service_label, internal_divider, login_endpoint, refresh_endpoint, outer_box_intact.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.6", prompt='Scale the app layer to 3 instances. Add "App-2" and "App-3" alongside App-1. Connect NGINX to all three with arrows.',
             source="""
+----------+     +--------+
|  NGINX   |---->| App-1  |
+----------+     +--------+
""",
             reference="""
                +----------+
                |  NGINX   |
                +----------+
                  |    |    |
                  v    v    v
              +--------+ +--------+ +--------+
              | App-1  | | App-2  | | App-3  |
              +--------+ +--------+ +--------+
""",
             assertions={"required_labels": ["NGINX", "App-1", "App-2", "App-3"], "forbidden_labels": [], "entity_count": 4, "required_edges": [{"from": "NGINX", "to": "App-1"}, {"from": "NGINX", "to": "App-2"}, {"from": "NGINX", "to": "App-3"}], "required_edge_labels": [], "preserved_elements": ["NGINX", "App-1"]},
             judge="TASK: Scale up (Task 3.6)\n\nCHECKLIST: nginx_present, app1_present, app2_added, app3_added, nginx_to_all_three, apps_same_level.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.7", prompt='Insert an "API Server" between Browser and Database. Remove the direct Browser-to-Database arrow. Add Browser→API Server and API Server→Database arrows.',
             source="""
+---------+     +----------+
| Browser |---->| Database |
+---------+     +----------+
""",
             reference="""
+---------+     +------------+     +----------+
| Browser |---->| API Server |---->| Database |
+---------+     +------------+     +----------+
""",
             assertions={"required_labels": ["Browser", "API Server", "Database"], "forbidden_labels": [], "entity_count": 3, "required_edges": [{"from": "Browser", "to": "API Server"}, {"from": "API Server", "to": "Database"}], "required_edge_labels": [], "preserved_elements": ["Browser", "Database"]},
             judge="TASK: Insert intermediary (Task 3.7)\n\nCHECKLIST: browser_present, database_present, api_server_added, browser_to_api, api_to_database, no_direct_browser_db.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.8", prompt='Reverse the arrow direction. It should now point from NodeB to NodeA.',
             source="""
+---------+     +---------+
|  NodeA  |---->|  NodeB  |
+---------+     +---------+
""",
             reference="""
+---------+<----+---------+
|  NodeA  |     |  NodeB  |
+---------+     +---------+
""",
             assertions={"required_labels": ["NodeA", "NodeB"], "forbidden_labels": [], "entity_count": 2, "required_edges": [{"from": "NodeB", "to": "NodeA"}], "required_edge_labels": [], "preserved_elements": ["NodeA", "NodeB"]},
             judge="TASK: Reverse arrow direction (Task 3.8)\n\nCHECKLIST: nodea_present, nodeb_present, arrow_reversed, no_right_arrow.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.9", prompt='Mark the Server as a failure point: change its corner characters from + to * and add the label "FAILED" directly below the Server box.',
             source="""
+--------+     +--------+     +------+
| Client |---->| Server |---->|  DB  |
+--------+     +--------+     +------+
""",
             reference="""
+--------+     *--------*     +------+
| Client |---->* Server *---->|  DB  |
+--------+     *--------*     +------+
               FAILED
""",
             assertions={"required_labels": ["Client", "Server", "DB", "FAILED"], "forbidden_labels": [], "entity_count": 3, "required_edges": [{"from": "Client", "to": "Server"}, {"from": "Server", "to": "DB"}], "required_edge_labels": [], "preserved_elements": ["Client", "DB"]},
             judge="TASK: Mark failure node (Task 3.9)\n\nCHECKLIST: client_plus_corners, db_plus_corners, server_star_corners, failed_label, connections_preserved.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.10", prompt='Merge the "Auth" and "Session" boxes into one box labeled "Auth+Session Service". Update all connections so the merged box connects to both "Users DB" and "Sessions DB".',
             source="""
+----------+     +-----------+
|  Auth    |     |  Session  |
+----------+     +-----------+
     |                 |
     v                 v
+----------+     +-----------+
| Users DB |     | Sessions  |
|          |     |    DB     |
+----------+     +-----------+
""",
             reference="""
          +----------------------+
          | Auth+Session Service |
          +----------------------+
               |          |
               v          v
         +----------+  +-------------+
         | Users DB |  | Sessions DB |
         +----------+  +-------------+
""",
             assertions={"required_labels": ["Auth+Session Service", "Users DB", "Sessions DB"], "forbidden_labels": ["Auth", "Session"], "entity_count": 3, "required_edges": [{"from": "Auth+Session Service", "to": "Users DB"}, {"from": "Auth+Session Service", "to": "Sessions DB"}], "required_edge_labels": [], "preserved_elements": ["Users DB", "Sessions DB"]},
             judge="TASK: Merge two services (Task 3.10)\n\nCHECKLIST: auth_absent, session_absent, merged_box, users_db_present, sessions_db_present, merged_to_users_db, merged_to_sessions_db.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.11", prompt='Add a "Follower-5" node connected from the Leader.',
             source="""
                +--------+
                | Leader |
                +--------+
                /   |   \\
               v    v    v
       +------------+ +------------+ +------------+
       | Follower-1 | | Follower-2 | | Follower-3 |
       +------------+ +------------+ +------------+
                           |
                           v
                      +------------+
                      | Follower-4 |
                      +------------+
""",
             reference="""
                +--------+
                | Leader |
                +--------+
             /    |    |    \\
            v     v    v     v
    +------------+ +------------+ +------------+ +------------+
    | Follower-1 | | Follower-2 | | Follower-3 | | Follower-5 |
    +------------+ +------------+ +------------+ +------------+
                           |
                           v
                      +------------+
                      | Follower-4 |
                      +------------+
""",
             assertions={"required_labels": ["Leader", "Follower-1", "Follower-2", "Follower-3", "Follower-4", "Follower-5"], "forbidden_labels": [], "entity_count": 6,
                         "required_edges": [{"from": "Leader", "to": "Follower-1"}, {"from": "Leader", "to": "Follower-2"}, {"from": "Leader", "to": "Follower-3"}, {"from": "Leader", "to": "Follower-4"}, {"from": "Leader", "to": "Follower-5"}],
                         "required_edge_labels": [], "preserved_elements": ["Leader", "Follower-1", "Follower-2", "Follower-3", "Follower-4"]},
             judge="TASK: Add follower to Raft cluster (Task 3.11)\n\nCHECKLIST: original_cluster_preserved, follower5_added, leader_to_follower5.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.12", prompt='Add the label "HTTP" to the first arrow, "gRPC" to the second, "SQL" to the third, "cache" to the fourth.',
             source="""
+---+--->+---+--->+---+--->+---+--->+---+
| A |    | B |    | C |    | D |    | E |
+---+    +---+    +---+    +---+    +---+
""",
             reference="""
 HTTP      gRPC       SQL      cache
+---+--->+---+--->+---+--->+---+--->+---+
| A |    | B |    | C |    | D |    | E |
+---+    +---+    +---+    +---+    +---+
""",
             assertions={"required_labels": ["A", "B", "C", "D", "E", "HTTP", "gRPC", "SQL", "cache"], "forbidden_labels": [], "entity_count": 5, "required_edges": [], "required_edge_labels": ["HTTP", "gRPC", "SQL", "cache"], "preserved_elements": ["A", "B", "C", "D", "E"]},
             judge="TASK: Label arrows (Task 3.12)\n\nCHECKLIST: four_labels_present_near_arrows, node_boxes_preserved.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.13", prompt='Swap positions: move Node A to the right and Node B to the left. Update the arrow direction accordingly.',
             source="""
+--------+     +--------+
| Node A |---->| Node B |
+--------+     +--------+
""",
             reference="""
+--------+     +--------+
| Node B |---->| Node A |
+--------+     +--------+
""",
             assertions={"required_labels": ["Node A", "Node B"], "forbidden_labels": [], "entity_count": 2, "required_edges": [{"from": "Node B", "to": "Node A"}], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Swap node positions (Task 3.13)\n\nCHECKLIST: node_b_left, node_a_right, arrow_b_to_a.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.14", prompt='Draw an outer grouping box around all three labeled "Region: EU". Do not modify the inner boxes.',
             source="""
+-----------+  +-----------+  +-----------+
| Service X |  | Service Y |  | Service Z |
+-----------+  +-----------+  +-----------+
""",
             reference="""
+-------------------------------------------+
|                Region: EU                 |
| +-----------+  +-----------+  +-----------+|
| | Service X |  | Service Y |  | Service Z ||
| +-----------+  +-----------+  +-----------+|
+-------------------------------------------+
""",
             assertions={"required_labels": ["Region: EU", "Service X", "Service Y", "Service Z"], "forbidden_labels": [], "entity_count": 4, "required_edges": [], "required_edge_labels": [], "preserved_elements": ["Service X", "Service Y", "Service Z"]},
             judge="TASK: Add grouping box (Task 3.14)\n\nCHECKLIST: outer_region_box, all_three_services_inside, inner_boxes_preserved.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.15", prompt='Remove Follower-3 and its connection from the Leader.',
             source="""
                +--------+
                | Leader |
                +--------+
           /   /   |   \   \\
          v   v    v    v   v
 +------------+ +------------+ +------------+ +------------+ +------------+
 | Follower-1 | | Follower-2 | | Follower-3 | | Follower-4 | | Follower-5 |
 +------------+ +------------+ +------------+ +------------+ +------------+
""",
             reference="""
                +--------+
                | Leader |
                +--------+
             /    |    |    \\
            v     v    v     v
    +------------+ +------------+ +------------+ +------------+
    | Follower-1 | | Follower-2 | | Follower-4 | | Follower-5 |
    +------------+ +------------+ +------------+ +------------+
""",
             assertions={"required_labels": ["Leader", "Follower-1", "Follower-2", "Follower-4", "Follower-5"], "forbidden_labels": ["Follower-3"], "entity_count": 5, "required_edges": [], "required_edge_labels": [], "preserved_elements": ["Leader", "Follower-1", "Follower-2", "Follower-4", "Follower-5"]},
             judge="TASK: Remove follower (Task 3.15)\n\nCHECKLIST: follower3_absent, leader_present, remaining_followers_preserved.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.16", prompt='Add a sidecar "Proxy" box directly below each app box. Connect each Proxy to "Mesh Control Plane" below.',
             source="""
+-------+   +-------+   +-------+
| App A |   | App B |   | App C |
+-------+   +-------+   +-------+
""",
             reference="""
+-------+   +-------+   +-------+
| App A |   | App B |   | App C |
+-------+   +-------+   +-------+
    |           |           |
    v           v           v
+-------+   +-------+   +-------+
| Proxy |   | Proxy |   | Proxy |
+-------+   +-------+   +-------+
    \           |           /
     \          |          /
      v         v         v
      +--------------------+
      | Mesh Control Plane |
      +--------------------+
""",
             assertions={"required_labels": ["App A", "App B", "App C", "Proxy", "Mesh Control Plane"], "forbidden_labels": [], "entity_count": 7, "required_edges": [], "required_edge_labels": [], "preserved_elements": ["App A", "App B", "App C"]},
             judge="TASK: Add sidecars (Task 3.16)\n\nCHECKLIST: three_proxies, app_to_proxy_links, proxies_to_control_plane.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.17", prompt='Change all three arrows to bidirectional.',
             source="""
+---+--->+---+--->+---+--->+---+
| A |    | B |    | C |    | D |
+---+    +---+    +---+    +---+
""",
             reference="""
+---+<--->+---+<--->+---+<--->+---+
| A |     | B |     | C |     | D |
+---+     +---+     +---+     +---+
""",
             assertions={"required_labels": ["A", "B", "C", "D"], "forbidden_labels": [], "entity_count": 4, "required_edges": [{"from": "A", "to": "B"}, {"from": "B", "to": "A"}, {"from": "B", "to": "C"}, {"from": "C", "to": "B"}, {"from": "C", "to": "D"}, {"from": "D", "to": "C"}], "required_edge_labels": [], "preserved_elements": ["A", "B", "C", "D"]},
             judge="TASK: Bidirectional conversion (Task 3.17)\n\nCHECKLIST: all_three_connectors_bidirectional.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.18", prompt='Swap the positions of B and C. Update arrows accordingly: A→C→B→D.',
             source="""
+---+--->+---+--->+---+--->+---+
| A |    | B |    | C |    | D |
+---+    +---+    +---+    +---+
""",
             reference="""
+---+--->+---+--->+---+--->+---+
| A |    | C |    | B |    | D |
+---+    +---+    +---+    +---+
""",
             assertions={"required_labels": ["A", "B", "C", "D"], "forbidden_labels": [], "entity_count": 4, "required_edges": [{"from": "A", "to": "C"}, {"from": "C", "to": "B"}, {"from": "B", "to": "D"}], "required_edge_labels": [], "preserved_elements": ["A", "B", "C", "D"]},
             judge="TASK: Swap B and C (Task 3.18)\n\nCHECKLIST: order_a_c_b_d, arrows_a_to_c_to_b_to_d.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.19", prompt='Add a version annotation inside each box on a new line: "v2.1", "v1.8", "v3.0" respectively.',
             source="""
+--------------+  +--------------+  +---------------+
| Auth Service |  | User Service |  | Order Service |
+--------------+  +--------------+  +---------------+
""",
             reference="""
+--------------+  +--------------+  +---------------+
| Auth Service |  | User Service |  | Order Service |
| v2.1         |  | v1.8         |  | v3.0          |
+--------------+  +--------------+  +---------------+
""",
             assertions={"required_labels": ["Auth Service", "User Service", "Order Service", "v2.1", "v1.8", "v3.0"], "forbidden_labels": [], "entity_count": 3, "required_edges": [], "required_edge_labels": [], "preserved_elements": ["Auth Service", "User Service", "Order Service"]},
             judge="TASK: Add version annotations (Task 3.19)\n\nCHECKLIST: all_three_service_boxes, correct_version_strings_inside_boxes.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("3.20", prompt='Split into two boxes side by side: "Write Primary" on the left and "Read Replica" on the right. Show an arrow from Write Primary to Read Replica labeled "replication".',
             source="""
+----------+
| Database |
+----------+
""",
             reference="""
 replication
+---------------+----->+--------------+
| Write Primary |      | Read Replica |
+---------------+      +--------------+
""",
             assertions={"required_labels": ["Write Primary", "Read Replica", "replication"], "forbidden_labels": ["Database"], "entity_count": 2, "required_edges": [{"from": "Write Primary", "to": "Read Replica"}], "required_edge_labels": ["replication"], "preserved_elements": []},
             judge="TASK: Split database node (Task 3.20)\n\nCHECKLIST: database_absent, two_new_boxes, replication_arrow_and_label.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.1", prompt='Draw the classic 3-tier web architecture:\n- "Client (Browser)" on the left\n- "Load Balancer (NGINX)" in the middle receiving traffic from Client\n- Three app servers in a column: "App-1", "App-2", "App-3" receiving traffic from LB\n- "PostgreSQL" database on the right receiving queries from all app servers\nShow arrows between each tier.',
             reference="""
+------------------+   +-----------------------+   +-------+   +------------+
| Client (Browser) |-->| Load Balancer (NGINX) |-->| App-1 |-->| PostgreSQL |
+------------------+   +-----------------------+   +-------+   +------------+
                                                  ->| App-2 |-->| PostgreSQL |
                                                  ->| App-3 |-->| PostgreSQL |
""",
             assertions={"required_labels": ["Client (Browser)", "Load Balancer (NGINX)", "App-1", "App-2", "App-3", "PostgreSQL"], "forbidden_labels": [], "entity_count": 6,
                         "required_edges": [{"from": "Client (Browser)", "to": "Load Balancer (NGINX)"}, {"from": "Load Balancer (NGINX)", "to": "App-1"}, {"from": "Load Balancer (NGINX)", "to": "App-2"}, {"from": "Load Balancer (NGINX)", "to": "App-3"}, {"from": "App-1", "to": "PostgreSQL"}, {"from": "App-2", "to": "PostgreSQL"}, {"from": "App-3", "to": "PostgreSQL"}],
                         "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: 3-tier web architecture (Task 4.1)\n\nCHECKLIST: client_box, lb_box, three_app_servers, postgres_box, client_to_lb, lb_to_all_three, all_apps_to_postgres, correct_left_to_right_flow.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.2", prompt='Draw a database read replica pattern:\n- "App Server" on the left\n- "Primary DB" in the middle — App Server writes to it (label arrow "write")\n- "Read Replica-1" and "Read Replica-2" to the right — App Server reads from both (label arrows "read")\n- Primary DB replicates to both replicas with dashed arrows labeled "async replication"',
             reference="""
 write
+------------+----->+------------+ - -async replication- -> +----------------+
| App Server |      | Primary DB |                          | Read Replica-1 |
+------------+      +------------+ - -async replication- -> +----------------+
      \\ read                                         \
       \\ read                                         -> +----------------+
        +----------------------------------------------->| Read Replica-2 |
                                                          +----------------+
""",
             assertions={"required_labels": ["App Server", "Primary DB", "Read Replica-1", "Read Replica-2", "write", "read", "async replication"], "forbidden_labels": [], "entity_count": 4, "required_edges": [{"from": "App Server", "to": "Primary DB"}, {"from": "App Server", "to": "Read Replica-1"}, {"from": "App Server", "to": "Read Replica-2"}, {"from": "Primary DB", "to": "Read Replica-1"}, {"from": "Primary DB", "to": "Read Replica-2"}], "required_edge_labels": ["write", "read", "async replication"], "preserved_elements": []},
             judge="TASK: Read replica pattern (Task 4.2)\n\nCHECKLIST: app_server, primary_db, replica_1, replica_2, write_to_primary, read_from_replicas, replication_arrows, direction_correct.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.3", prompt='Draw a CI/CD pipeline as a left-to-right chain with these stages in order:\n"Code Push" → "Build" → "Unit Tests" → "Integration Tests" → "Staging Deploy" → "Prod Deploy"\nAlso show a dashed "rollback" arrow from "Prod Deploy" back to "Staging Deploy" labeled "on failure".',
             reference="""
+-----------+->+-------+->+------------+->+-------------------+->+----------------+->+-------------+
| Code Push |  | Build |  | Unit Tests |  | Integration Tests |  | Staging Deploy |  | Prod Deploy |
+-----------+  +-------+  +------------+  +-------------------+  +----------------+  +-------------+
                                                                  ^                      |
                                                                  | - - on failure - - -+
""",
             assertions={"required_labels": ["Code Push", "Build", "Unit Tests", "Integration Tests", "Staging Deploy", "Prod Deploy", "on failure"], "forbidden_labels": [], "entity_count": 6, "required_edges": [{"from": "Code Push", "to": "Build"}, {"from": "Build", "to": "Unit Tests"}, {"from": "Unit Tests", "to": "Integration Tests"}, {"from": "Integration Tests", "to": "Staging Deploy"}, {"from": "Staging Deploy", "to": "Prod Deploy"}, {"from": "Prod Deploy", "to": "Staging Deploy"}], "required_edge_labels": ["on failure"], "preserved_elements": []},
             judge="TASK: CI/CD pipeline (Task 4.3)\n\nCHECKLIST: all_six_stages, correct_order, forward_arrows, rollback_arrow, on_failure_label, rollback_visual_distinction.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.4", prompt='Draw a CDN architecture:\n- "Users (Global)" on the left\n- Two edge cache nodes in the middle: "Edge Cache (US)" and "Edge Cache (EU)"\n- "Origin Server" on the right\n- Users connect to both edge nodes (label "cached response")\n- Both edge nodes connect to Origin Server (label "cache miss")',
             reference="""
 cached response                 cache miss
+----------------+------------->+-----------------+------------->+---------------+
| Users (Global) |              | Edge Cache (US) |              | Origin Server |
+----------------+              +-----------------+              +---------------+
       \\ cached response                cache miss /
        +------------------------------>+-----------------+
                                         | Edge Cache (EU) |
                                         +-----------------+
""",
             assertions={"required_labels": ["Users (Global)", "Edge Cache (US)", "Edge Cache (EU)", "Origin Server", "cached response", "cache miss"], "forbidden_labels": [], "entity_count": 4, "required_edges": [{"from": "Users (Global)", "to": "Edge Cache (US)"}, {"from": "Users (Global)", "to": "Edge Cache (EU)"}, {"from": "Edge Cache (US)", "to": "Origin Server"}, {"from": "Edge Cache (EU)", "to": "Origin Server"}], "required_edge_labels": ["cached response", "cache miss"], "preserved_elements": []},
             judge="TASK: CDN architecture (Task 4.4)\n\nCHECKLIST: users_box, edge_us, edge_eu, origin, users_to_both_edges, edges_to_origin, cached_response_label, cache_miss_label, no_direct_users_to_origin.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.5", prompt='Draw a URL shortener system architecture:\n- "Client" → "Load Balancer" → two "App Server" boxes\n- App Servers check "Redis Cache" first (label arrow "cache hit / O(1)")\n- On cache miss, App Servers query "Cassandra DB" (label arrow "cache miss")\n- App Servers write click events to "Kafka"\n- "Analytics Service" consumes from Kafka',
             reference="""
+--------+->+---------------+->+-------------+   +-------------+
| Client |  | Load Balancer |  | App Server1 |   | App Server2 |
+--------+  +---------------+  +-------------+   +-------------+
                           |           |  \\ cache miss      |  \\ cache miss
                           |           |   v                 |   v
                           |           | +--------------+    | +--------------+
                           |           | | Cassandra DB |    | | Cassandra DB |
                           |           | +--------------+    | +--------------+
                           |           | -> Redis Cache      | -> Redis Cache
                           |           | cache hit / O(1)    | cache hit / O(1)
                           |           v                     v
                           |         +-------+------------->+-------------------+
                           |         | Kafka |              | Analytics Service |
                           |         +-------+              +-------------------+
""",
             assertions={"required_labels": ["Client", "Load Balancer", "App Server", "Redis Cache", "Cassandra DB", "Kafka", "Analytics Service"], "forbidden_labels": [], "entity_count": 8, "required_edges": [{"from": "Client", "to": "Load Balancer"}, {"from": "Load Balancer", "to": "App Server"}, {"from": "App Server", "to": "Redis Cache"}, {"from": "App Server", "to": "Cassandra DB"}, {"from": "App Server", "to": "Kafka"}, {"from": "Kafka", "to": "Analytics Service"}], "required_edge_labels": ["cache hit", "cache miss"], "preserved_elements": []},
             judge="TASK: URL shortener architecture (Task 4.5)\n\nCHECKLIST: client_to_lb, lb_to_apps, redis_cache, cassandra, kafka, analytics, cache_hit_label, cache_miss_label, app_to_redis_direction, kafka_to_analytics.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.6", prompt='Draw a rate limiter architecture:\n- "Client" → "Rate Limiter" service\n- Rate Limiter checks "Redis (token bucket counters)"\n- Allowed requests: Rate Limiter → "App Server"\n- Rejected requests: Rate Limiter → Client with dashed arrow labeled "429 Too Many Requests"',
             reference="""
+--------+----->+--------------+----->+------------+
| Client |      | Rate Limiter |      | App Server |
+--------+< - - +--------------+      +------------+
                 |                           ^
                 v                           |
      +-------------------------------+      |
      | Redis (token bucket counters) |      |
      +-------------------------------+      |
         429 Too Many Requests - - - -+------+
""",
             assertions={"required_labels": ["Client", "Rate Limiter", "Redis (token bucket counters)", "App Server", "429 Too Many Requests"], "forbidden_labels": [], "entity_count": 4, "required_edges": [{"from": "Client", "to": "Rate Limiter"}, {"from": "Rate Limiter", "to": "Redis (token bucket counters)"}, {"from": "Rate Limiter", "to": "App Server"}, {"from": "Rate Limiter", "to": "Client"}], "required_edge_labels": ["429 Too Many Requests"], "preserved_elements": []},
             judge="TASK: Rate limiter (Task 4.6)\n\nCHECKLIST: client_box, rate_limiter, redis_counter, app_server, client_to_rl, rl_to_redis, rl_to_app, rl_to_client_reject, 429_label.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.7", prompt='Draw a notification system:\n- Three event sources publish to "Kafka": "Order Service", "Payment Service", "Shipping Service"\n- "Notification Service" consumes from Kafka and checks "User Preferences DB"\n- Notification Service delivers to three channels: "Email Service", "SMS Service", "Push Service"\n- Each channel connects to its provider: Email → "SendGrid", SMS → "Twilio", Push → "FCM"',
             reference="""
+---------------+ +-----------------+ +------------------+
| Order Service | | Payment Service | | Shipping Service |
+---------------+ +-----------------+ +------------------+
        \               |                /
         \              |               /
          v             v              v
                  +-------+
                  | Kafka |
                  +-------+
                      |
                      v
          +----------------------+
          | Notification Service |
          +----------------------+
             |       |        |      \\
             v       v        v       v
 +---------------+ +-------------+ +--------------+ +---------------------+
 | Email Service | | SMS Service | | Push Service | | User Preferences DB |
 +---------------+ +-------------+ +--------------+ +---------------------+
       |                |                |
       v                v                v
 +----------+      +--------+      +------+
 | SendGrid |      | Twilio |      | FCM  |
 +----------+      +--------+      +------+
""",
             assertions={"required_labels": ["Order Service", "Payment Service", "Shipping Service", "Kafka", "Notification Service", "User Preferences DB", "Email Service", "SMS Service", "Push Service", "SendGrid", "Twilio", "FCM"], "forbidden_labels": [], "entity_count": 12, "required_edges": [{"from": "Order Service", "to": "Kafka"}, {"from": "Payment Service", "to": "Kafka"}, {"from": "Shipping Service", "to": "Kafka"}, {"from": "Kafka", "to": "Notification Service"}, {"from": "Notification Service", "to": "User Preferences DB"}, {"from": "Notification Service", "to": "Email Service"}, {"from": "Notification Service", "to": "SMS Service"}, {"from": "Notification Service", "to": "Push Service"}, {"from": "Email Service", "to": "SendGrid"}, {"from": "SMS Service", "to": "Twilio"}, {"from": "Push Service", "to": "FCM"}], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Notification system (Task 4.7)\n\nCHECKLIST: three_sources, kafka, notification_service, user_prefs_db, three_channels, three_providers, sources_to_kafka, kafka_to_notification, notification_to_channels, channels_to_providers.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.8", prompt='Draw a microservices API gateway pattern:\n- "Mobile Client" and "Web Client" both connect to "API Gateway"\n- Inside the API Gateway box, show two sub-components: "Auth Middleware" and "Rate Limiter"\n- Gateway routes to three backend services, each with its own DB:\n  - "User Service" with "Users DB"\n  - "Product Service" with "Products DB"\n  - "Order Service" with "Orders DB"',
             reference="""
+---------------+   +------------------------------+   +--------------+   +----------+
| Mobile Client |-->|         API Gateway          |-->| User Service |-->| Users DB |
+---------------+   | +------------------------+   |   +--------------+   +----------+
                    | | Auth Middleware        |   |
+------------+----->| | Rate Limiter          |---|-->| Product Service |->| Products DB |
| Web Client |      | +------------------------+   |  +----------------+  +-------------+
+------------+      +------------------------------+-->| Order Service |-->| Orders DB |
                                                         +---------------+   +-----------+
""",
             assertions={"required_labels": ["Mobile Client", "Web Client", "API Gateway", "Auth Middleware", "Rate Limiter", "User Service", "Users DB", "Product Service", "Products DB", "Order Service", "Orders DB"], "forbidden_labels": [], "entity_count": 9, "required_edges": [{"from": "Mobile Client", "to": "API Gateway"}, {"from": "Web Client", "to": "API Gateway"}, {"from": "API Gateway", "to": "User Service"}, {"from": "API Gateway", "to": "Product Service"}, {"from": "API Gateway", "to": "Order Service"}, {"from": "User Service", "to": "Users DB"}, {"from": "Product Service", "to": "Products DB"}, {"from": "Order Service", "to": "Orders DB"}], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Microservices API gateway (Task 4.8)\n\nCHECKLIST: mobile_client, web_client, api_gateway, auth_inside_gateway, rate_limiter_inside_gateway, three_services, three_dbs, both_clients_to_gateway, gateway_to_all_services, each_service_own_db.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.9", prompt='Draw a Dropbox-style file storage system:\n- "Client (Desktop)" uploads to "Upload Service"\n- Upload Service stores file chunks in "S3 (Block Store)" and metadata in "Metadata DB (PostgreSQL)"\n- "Download Service" reads from both S3 and Metadata DB to serve files to Client\n- "Sync Service" connects to "Notification Queue (Kafka)" to send change notifications to Client',
             reference="""
+------------------+--->+----------------+--->+------------------+
| Client (Desktop) |    | Upload Service |    | S3 (Block Store) |
+------------------+    +----------------+    +------------------+
                                  \                ^
                                   \               |
                                    v              |
                             +--------------------------+
                             | Metadata DB (PostgreSQL) |
                             +--------------------------+
                                        ^         ^
                                        |         |
                           +----------------+     |
                           | Download Service|----+
                           +----------------+
                                  |
                                  v
                         +--------------------------+
                         | Notification Queue (Kafka)|
                         +--------------------------+
                                  ^
                                  |
                           +-------------+
                           | Sync Service|
                           +-------------+
""",
             assertions={"required_labels": ["Client (Desktop)", "Upload Service", "S3 (Block Store)", "Metadata DB (PostgreSQL)", "Download Service", "Sync Service", "Notification Queue (Kafka)"], "forbidden_labels": [], "entity_count": 7, "required_edges": [{"from": "Client (Desktop)", "to": "Upload Service"}, {"from": "Upload Service", "to": "S3 (Block Store)"}, {"from": "Upload Service", "to": "Metadata DB (PostgreSQL)"}, {"from": "Download Service", "to": "S3 (Block Store)"}, {"from": "Download Service", "to": "Metadata DB (PostgreSQL)"}, {"from": "Download Service", "to": "Client (Desktop)"}, {"from": "Sync Service", "to": "Notification Queue (Kafka)"}, {"from": "Notification Queue (Kafka)", "to": "Client (Desktop)"}], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Dropbox-style file storage (Task 4.9)\n\nCHECKLIST: client, upload_service, s3, metadata_db, download_service, sync_service, kafka, upload_to_s3, upload_to_metadata, download_reads_both.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.10", prompt='Draw a search autocomplete system:\n- "User" types into "Search API"\n- Search API checks "Trie Cache (In-Memory)" first\n- On miss, Search API queries "Prefix Index (Elasticsearch)"\n- "Data Aggregation Service" reads "Query Logs DB" and rebuilds both the Trie Cache and Prefix Index periodically\n- Results flow back from Search API to User',
             reference="""
+------+<----+------------+
| User |     | Search API |
+------+---->+------------+
               |       \\
               v        v
 +-----------------------+   +-----------------------------+
 | Trie Cache (In-Memory)|   | Prefix Index (Elasticsearch)|
 +-----------------------+   +-----------------------------+
               ^                     ^
               |                     |
        +-------------------------+  |
        | Data Aggregation Service|--+
        +-------------------------+
                    |
                    v
             +---------------+
             | Query Logs DB |
             +---------------+
""",
             assertions={"required_labels": ["User", "Search API", "Trie Cache (In-Memory)", "Prefix Index (Elasticsearch)", "Data Aggregation Service", "Query Logs DB"], "forbidden_labels": [], "entity_count": 6, "required_edges": [{"from": "User", "to": "Search API"}, {"from": "Search API", "to": "Trie Cache (In-Memory)"}, {"from": "Search API", "to": "Prefix Index (Elasticsearch)"}, {"from": "Search API", "to": "User"}, {"from": "Data Aggregation Service", "to": "Query Logs DB"}, {"from": "Data Aggregation Service", "to": "Trie Cache (In-Memory)"}, {"from": "Data Aggregation Service", "to": "Prefix Index (Elasticsearch)"}], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Search autocomplete (Task 4.10)\n\nCHECKLIST: user, search_api, trie_cache, elasticsearch, aggregation_service, query_logs, hot_path_trie, cold_path_es, response_to_user, background_rebuild.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.11", prompt='Draw the Twitter news feed architecture with hybrid fan-out:\n- "User" posts via "Tweet Service" which writes to "Tweets DB (Cassandra)"\n- Tweet Service publishes to "Fan-out Service" via "Kafka"\n- Fan-out Service reads "Social Graph DB" to find followers\n- Fan-out Service writes to "Feed Cache (Redis)" for normal users — label this path "fan-out on write"\n- For celebrity accounts: "Feed Service" reads directly from Tweets DB — label this path "fan-out on read"\n- User reads their timeline via "Feed Service" which checks Feed Cache first',
             reference="""
+------+---->+---------------+---->+------------------------+
| User |     | Tweet Service |     | Tweets DB (Cassandra) |
+------+     +---------------+     +------------------------+
                  |
                  v
               +-------+---->+-----------------+---->+--------------------+
               | Kafka |     | Fan-out Service |     | Social Graph DB    |
               +-------+     +-----------------+     +--------------------+
                                      |
                                      | fan-out on write
                                      v
                               +-------------------+
                               | Feed Cache (Redis)|
                               +-------------------+
                                      ^
                                      |
                                 +--------------+
                                 | Feed Service |
                                 +--------------+
                                    | fan-out on read
                                    v
                           +------------------------+
                           | Tweets DB (Cassandra) |
                           +------------------------+
""",
             assertions={"required_labels": ["User", "Tweet Service", "Tweets DB (Cassandra)", "Kafka", "Fan-out Service", "Social Graph DB", "Feed Cache (Redis)", "Feed Service", "fan-out on write", "fan-out on read"], "forbidden_labels": [], "entity_count": 9, "required_edges": [{"from": "User", "to": "Tweet Service"}, {"from": "Tweet Service", "to": "Tweets DB (Cassandra)"}, {"from": "Tweet Service", "to": "Kafka"}, {"from": "Kafka", "to": "Fan-out Service"}, {"from": "Fan-out Service", "to": "Social Graph DB"}, {"from": "Fan-out Service", "to": "Feed Cache (Redis)"}, {"from": "Feed Service", "to": "Feed Cache (Redis)"}, {"from": "Feed Service", "to": "Tweets DB (Cassandra)"}, {"from": "Feed Service", "to": "User"}], "required_edge_labels": ["fan-out on write", "fan-out on read"], "preserved_elements": []},
             judge="TASK: Twitter news feed hybrid fan-out (Task 4.11)\n\nCHECKLIST: tweet_service, cassandra, kafka, fanout_service, social_graph, feed_cache, feed_service, write_path_complete, fan_out_on_write_label, fan_out_on_read_label, celebrity_bypass, two_paths_distinct.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.12", prompt='Draw a video upload and streaming pipeline:\n- "User" uploads raw video to "Upload Service"\n- Upload Service stores in "Raw Storage (S3)" and queues a job in "Transcoding Queue (Kafka)"\n- Three "Transcoder Worker" boxes consume from Kafka and write output to "Processed Storage (S3)"\n- "CDN" pulls from Processed Storage and serves video to User\n- "Metadata Service" updates "Video DB" at each processing stage',
             reference="""
+------+---->+----------------+---->+------------------+
| User |     | Upload Service |     | Raw Storage (S3) |
+------+     +----------------+     +------------------+
                   |
                   v
         +--------------------------+
         | Transcoding Queue (Kafka)|
         +--------------------------+
            |          |          |
            v          v          v
    +----------------+ +----------------+ +----------------+
    |TranscoderWorker| |TranscoderWorker| |TranscoderWorker|
    +----------------+ +----------------+ +----------------+
            \            |            /
             \           |           /
              v          v          v
              +------------------------+
              | Processed Storage (S3) |
              +------------------------+
                         |
                         v
                      +-----+
                      | CDN |
                      +-----+
                         |
                         v
                      +------+
                      | User |
                      +------+
         +------------------+---->+----------+
         | Metadata Service |     | Video DB |
         +------------------+---->+----------+
""",
             assertions={"required_labels": ["User", "Upload Service", "Raw Storage (S3)", "Transcoding Queue (Kafka)", "Transcoder Worker", "Processed Storage (S3)", "CDN", "Metadata Service", "Video DB"], "forbidden_labels": [], "entity_count": 10, "required_edges": [{"from": "User", "to": "Upload Service"}, {"from": "Upload Service", "to": "Raw Storage (S3)"}, {"from": "Upload Service", "to": "Transcoding Queue (Kafka)"}, {"from": "Transcoding Queue (Kafka)", "to": "Transcoder Worker"}, {"from": "Transcoder Worker", "to": "Processed Storage (S3)"}, {"from": "Processed Storage (S3)", "to": "CDN"}, {"from": "CDN", "to": "User"}, {"from": "Metadata Service", "to": "Video DB"}], "required_edge_labels": [], "preserved_elements": []},
             judge="TASK: Video upload pipeline (Task 4.12)\n\nCHECKLIST: upload_service, raw_s3, kafka_queue, transcoder_workers, processed_s3, cdn, metadata_service, video_db, upload_to_raw_s3, kafka_to_workers, workers_to_processed, cdn_to_user.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.13", prompt='Draw a real-time chat system:\n- "User A" and "User B" each connected to "Chat Server" via WebSocket (label connections "WebSocket")\n- Chat Server publishes to "Message Queue (Kafka)"\n- "Message Service" consumes from Kafka and writes to "Messages DB (Cassandra)"\n- "Presence Service" tracks online status in "Presence Cache (Redis)"\n- Chat Server checks Presence Service before routing\n- For offline users: "Push Notification Service" sends via "APNs / FCM"',
             reference="""
 WebSocket                       WebSocket
+--------+<-------------------->+-------------+<-------------------->+--------+
| User A |                      | Chat Server |                      | User B |
+--------+                      +-------------+                      +--------+
                                      |   \\
                                      |    v
                                      | +--------------------+
                                      | | Presence Service   |
                                      | +--------------------+
                                      |          |
                                      |          v
                                      |   +-----------------------+
                                      |   | Presence Cache (Redis)|
                                      |   +-----------------------+
                                      v
                              +-----------------------+
                              | Message Queue (Kafka) |
                              +-----------------------+
                                      |
                                      v
                           +------------------------+---->+-------------------------+
                           | Message Service        |     | Messages DB (Cassandra) |
                           +------------------------+     +-------------------------+
                                      |
                                      v
                           +--------------------------+---->+-----------+
                           | Push Notification Service|     | APNs / FCM|
                           +--------------------------+     +-----------+
""",
             assertions={"required_labels": ["User A", "User B", "Chat Server", "Message Queue (Kafka)", "Message Service", "Messages DB (Cassandra)", "Presence Service", "Presence Cache (Redis)", "Push Notification Service", "APNs / FCM", "WebSocket"], "forbidden_labels": [], "entity_count": 10, "required_edges": [{"from": "User A", "to": "Chat Server"}, {"from": "User B", "to": "Chat Server"}, {"from": "Chat Server", "to": "Message Queue (Kafka)"}, {"from": "Message Queue (Kafka)", "to": "Message Service"}, {"from": "Message Service", "to": "Messages DB (Cassandra)"}, {"from": "Chat Server", "to": "Presence Service"}, {"from": "Presence Service", "to": "Presence Cache (Redis)"}, {"from": "Chat Server", "to": "Push Notification Service"}, {"from": "Push Notification Service", "to": "APNs / FCM"}], "required_edge_labels": ["WebSocket"], "preserved_elements": []},
             judge="TASK: Chat system (Task 4.13)\n\nCHECKLIST: user_a, user_b, chat_server, websocket_label, kafka, message_service, cassandra, presence_service, redis_presence, push_notification, apns_fcm, bidirectional_users.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.14", prompt='Draw a ride-sharing backend (Uber-style):\n- "Rider App" and "Driver App" both connect to "API Gateway"\n- "Location Service" receives GPS pings from Driver App via WebSocket, stores in "Location Cache (Redis)" with geohash label\n- "Matching Service" reads from Location Cache to find nearby drivers, creates trips in "Trips DB"\n- "Payment Service" processes payments, writes to "Payments DB" and external "Stripe"\n- "Notification Service" sends status updates to both apps',
             reference="""
+-----------+      +-------------+      +------------+
| Rider App |----->| API Gateway |<-----| Driver App |
+-----------+      +-------------+      +------------+
                                               |
                                               | WebSocket / geohash
                                               v
                                      +------------------+---->+------------------------+
                                      | Location Service |     | Location Cache (Redis) |
                                      +------------------+     +------------------------+
                                                           ^          |
                                                           |          v
                                                  +----------------+ +----------+
                                                  | Matching Service| | Trips DB|
                                                  +----------------+ +----------+
                                                  +----------------+---->+-------------+---->+--------+
                                                  | Payment Service |     | Payments DB |     | Stripe |
                                                  +----------------+     +-------------+     +--------+
                                                  +--------------------+
                                                  | Notification Service|
                                                  +--------------------+
                                                     |              |
                                                     v              v
                                                 +-----------+   +------------+
                                                 | Rider App |   | Driver App |
                                                 +-----------+   +------------+
""",
             assertions={"required_labels": ["Rider App", "Driver App", "API Gateway", "Location Service", "Location Cache (Redis)", "Matching Service", "Trips DB", "Payment Service", "Payments DB", "Stripe", "Notification Service", "geohash"], "forbidden_labels": [], "entity_count": 11, "required_edges": [{"from": "Rider App", "to": "API Gateway"}, {"from": "Driver App", "to": "API Gateway"}, {"from": "Driver App", "to": "Location Service"}, {"from": "Location Service", "to": "Location Cache (Redis)"}, {"from": "Matching Service", "to": "Location Cache (Redis)"}, {"from": "Matching Service", "to": "Trips DB"}, {"from": "Payment Service", "to": "Payments DB"}, {"from": "Payment Service", "to": "Stripe"}, {"from": "Notification Service", "to": "Rider App"}, {"from": "Notification Service", "to": "Driver App"}], "required_edge_labels": ["geohash"], "preserved_elements": []},
             judge="TASK: Ride-sharing backend (Task 4.14)\n\nCHECKLIST: rider_app, driver_app, api_gateway, location_service, location_redis, geohash_label, matching_service, trips_db, payment_service, stripe, notification_service, notification_to_both.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
    add_task("4.15", prompt='Draw a Lambda architecture data pipeline:\n- Three data sources publish to "Kafka (Event Stream)": "App Events", "DB Change Stream", "IoT Sensors"\n- Speed layer: Kafka → "Stream Processor (Flink)" → "Time-Series DB" — label "speed layer"\n- Batch layer: Kafka → "Batch Processor (Spark)" → "Data Warehouse (BigQuery)" — label "batch layer"\n- Both outputs feed "Analytics Dashboard"\n- "Data Catalog" connects to both storage layers',
             reference="""
+------------+ +------------------+ +-------------+
| App Events | | DB Change Stream | | IoT Sensors |
+------------+ +------------------+ +-------------+
      \              |                /
       \             |               /
        v            v              v
               +----------------------+
               | Kafka (Event Stream) |
               +----------------------+
                  | speed layer    | batch layer
                  v                v
   +--------------------------+  +-------------------------+
   | Stream Processor (Flink) |  | Batch Processor (Spark) |
   +--------------------------+  +-------------------------+
                  |                |
                  v                v
       +----------------+    +-----------------------------+
       | Time-Series DB |    | Data Warehouse (BigQuery)   |
       +----------------+    +-----------------------------+
                  \                /
                   \              /
                    v            v
                 +----------------------+
                 | Analytics Dashboard  |
                 +----------------------+
                 +-------------+
                 | Data Catalog|
                 +-------------+
                    |      |
                    v      v
           +----------------+  +-----------------------------+
           | Time-Series DB |  | Data Warehouse (BigQuery)   |
           +----------------+  +-----------------------------+
""",
             assertions={"required_labels": ["App Events", "DB Change Stream", "IoT Sensors", "Kafka (Event Stream)", "Stream Processor (Flink)", "Time-Series DB", "Batch Processor (Spark)", "Data Warehouse (BigQuery)", "Analytics Dashboard", "Data Catalog", "speed layer", "batch layer"], "forbidden_labels": [], "entity_count": 10, "required_edges": [{"from": "App Events", "to": "Kafka (Event Stream)"}, {"from": "DB Change Stream", "to": "Kafka (Event Stream)"}, {"from": "IoT Sensors", "to": "Kafka (Event Stream)"}, {"from": "Kafka (Event Stream)", "to": "Stream Processor (Flink)"}, {"from": "Kafka (Event Stream)", "to": "Batch Processor (Spark)"}, {"from": "Stream Processor (Flink)", "to": "Time-Series DB"}, {"from": "Batch Processor (Spark)", "to": "Data Warehouse (BigQuery)"}, {"from": "Time-Series DB", "to": "Analytics Dashboard"}, {"from": "Data Warehouse (BigQuery)", "to": "Analytics Dashboard"}, {"from": "Data Catalog", "to": "Time-Series DB"}, {"from": "Data Catalog", "to": "Data Warehouse (BigQuery)"}], "required_edge_labels": ["speed layer", "batch layer"], "preserved_elements": []},
             judge="TASK: Lambda architecture (Task 4.15)\n\nCHECKLIST: three_sources, kafka, flink, spark, timeseries_db, bigquery, dashboard, data_catalog, speed_layer_label, batch_layer_label, kafka_forks_both, both_to_dashboard.\n\nMODEL OUTPUT:\n---\n{model_output}\n---\n\nRESPOND: {\"scores\": {...}, \"total\": 0, \"pass\": false, \"reason\": \"string\"}")
def main() -> None:
    populate_tasks()
    for script_name, content in {
        "render.py": SCRIPT_RENDER,
        "render_all.py": SCRIPT_RENDER_ALL,
        "renderers/render_ascii.mjs": SCRIPT_RENDER_ASCII_MJS,
        "lib/checker.py": SCRIPT_CHECKER,
        "lib/__init__.py": "",
        "eval.py": (ROOT / "scripts" / "eval.py").read_text(),
        "lib/fireworks_api.py": (ROOT / "scripts" / "lib" / "fireworks_api.py").read_text(),
        "run_model.py": (ROOT / "scripts" / "run_model.py").read_text(),
        "smoke_generate.py": (ROOT / "scripts" / "smoke_generate.py").read_text(),
        "run_vlm_judge.py": (ROOT / "scripts" / "run_vlm_judge.py").read_text(),
        "run_vlm_judge_instructor.py": (
            ROOT / "scripts" / "run_vlm_judge_instructor.py"
        ).read_text(),
    }.items():
        write(SCRIPTS_DIR / script_name, content)

    oneshots = {
        "c1_example.txt": """
EXAMPLE PROMPT:
Draw two boxes "Alpha" and "Beta" connected left-to-right with an arrow.

EXAMPLE OUTPUT:
+---------+     +--------+
|  Alpha  |---->|  Beta  |
+---------+     +--------+
""",
        "c2_example.txt": """
EXAMPLE PROMPT:
Draw a simple client-server diagram: one "Browser" box connecting with an arrow to one "Web Server" box.

EXAMPLE OUTPUT:
+-----------+          +------------+
|  Browser  |--------->| Web Server |
+-----------+          +------------+
""",
        "c3_example.txt": """
EXAMPLE:
You will be shown an image of an ASCII diagram. Apply the given instruction
and output the modified diagram as plain text.

EXAMPLE SOURCE DIAGRAM:
+---------+     +---------+
| Alpha   |---->|  Beta   |
+---------+     +---------+

EXAMPLE INSTRUCTION:
Add a box labeled "Gamma" to the right of Beta, connected from Beta.

EXAMPLE OUTPUT:
+---------+     +---------+     +---------+
| Alpha   |---->|  Beta   |---->|  Gamma  |
+---------+     +---------+     +---------+
""",
        "c4_example.txt": """
EXAMPLE PROMPT:
Draw a 2-tier architecture: "Client" on the left sends requests to "Web Server" on the right.

EXAMPLE OUTPUT:
+--------+     HTTP      +------------+
| Client |-------------->| Web Server |
+--------+               +------------+
""",
    }
    for name, content in oneshots.items():
        write(ONESHOT_DIR / name, dedent(content).strip("\n"))

    for task_id, data in TASKS.items():
        category = task_id.split(".", 1)[0]
        td = TASKS_DIR / TASK_CATEGORY_DIRS.get(category, category) / task_id
        write(td / "prompt.txt", data["prompt"])
        write(td / "reference.ascii", dedent(data["reference"]).strip("\n"))
        write_json(td / "assertions.json", data["assertions"])
        write(td / "vlm_judge_prompt.txt", dedent(data["judge"]).strip("\n"))
        if data.get("source") is not None:
            write(td / "source.ascii", dedent(data["source"]).strip("\n"))


if __name__ == "__main__":
    main()
