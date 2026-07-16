from __future__ import annotations

import json
import re
from textwrap import dedent


COMMON_PROMPT_SUFFIX = (
    " Return only the final ASCII diagram in plain text. "
    "Do not include markdown fences, explanations, or any extra text."
)

ARROW_PROMPT_SUFFIX = (
    " When arrows are required, make them centered and aligned cleanly to their source and target. "
    "If an arrow has a label, place the label a little above the arrow rather than inside the arrow line. "
    "For any label or text inside a node, box, or icon, center it within that component whenever possible. "
    "Any component with incoming or outgoing arrows should be sized wide or tall enough to make those connections visually unambiguous, so it is clear where arrows originate and where they terminate. "
    "If one component fans out to multiple arrows, or multiple arrows converge into one component, its width or height should clearly support those attachment points."
)

EDITING_PROMPT_SUFFIX = (
    " Strictly apply only the requested edits and do not make any other changes outside them."
)


def strip_task_prompt_suffix(task_id: str, prompt: str) -> str:
    prompt = prompt.rstrip()
    common_suffix = COMMON_PROMPT_SUFFIX.strip()
    editing_suffix = EDITING_PROMPT_SUFFIX.strip()

    if prompt.endswith(common_suffix):
        prompt = prompt[: -len(common_suffix)].rstrip()
    if task_id.startswith("3.") and prompt.endswith(editing_suffix):
        prompt = prompt[: -len(editing_suffix)].rstrip()
    return prompt


def task_uses_arrows(assertions: dict) -> bool:
    if assertions.get("required_edges"):
        return True
    if assertions.get("required_edge_labels"):
        return True
    editing = assertions.get("editing", {})
    if editing.get("required_edge_labels"):
        return True
    return False


def split_prompt_items(text: str) -> list[str]:
    normalized = " ".join(text.split())
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", normalized)
        if item.strip()
    ]


def render_prompt_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def finalize_task_prompt(task_id: str, prompt: str, assertions: dict) -> str:
    prompt = strip_task_prompt_suffix(task_id, prompt.strip())
    prefix = "Draw an ASCII diagram illustrating "
    if not prompt.startswith(prefix):
        if prompt.startswith("Draw "):
            prompt = prefix + prompt[5:].lstrip()
        else:
            prompt = prefix + prompt[0].lower() + prompt[1:]

    prompt_items = split_prompt_items(prompt)
    if task_uses_arrows(assertions):
        prompt_items.extend(split_prompt_items(ARROW_PROMPT_SUFFIX.strip()))
    if task_id.startswith("3."):
        prompt_items.extend(split_prompt_items(EDITING_PROMPT_SUFFIX.strip()))
    prompt_items.extend(split_prompt_items(COMMON_PROMPT_SUFFIX.strip()))
    return render_prompt_bullets(prompt_items)


def normalize_assertions(task_id: str, assertions: dict) -> dict:
    normalized = dict(assertions)
    if task_id.startswith("3."):
        editing = normalized.get("editing", {}).copy()
        if "required_edge_labels" in normalized:
            editing.setdefault(
                "required_edge_labels",
                normalized.pop("required_edge_labels"),
            )
        if "preserved_elements" in normalized:
            editing.setdefault(
                "preserved_elements",
                normalized.pop("preserved_elements"),
            )
        normalized["editing"] = editing
    return normalized


def build_judge_prompt(
    task_id: str,
    prompt: str,
    assertions: dict,
    source: str | None = None,
) -> str:
    is_edit_task = source is not None
    source_section = ""
    if source is not None:
        source_section = (
            "\nSOURCE DIAGRAM ASCII (for edit tasks):\n---\n"
            + dedent(source).strip("\n")
            + "\n---\n"
        )

    has_required_edge_labels = bool(assertions.get("required_edge_labels")) or bool(
        assertions.get("editing", {}).get("required_edge_labels")
    )

    structural_fields = [
        "required_labels_present: list of labels from `required_labels` that are clearly present in the model output",
        "entity_count_observed: integer count of entities/nodes/boxes observed in the model output",
        "required_edges_present: list of edges from `required_edges` that are clearly present in the model output, using the same `{from, to}` strings as the assertions JSON",
    ]
    if has_required_edge_labels:
        structural_fields.append(
            "required_edge_labels_present: list of labels from `required_edge_labels` that are clearly present"
        )
    if is_edit_task:
        structural_fields.extend(
            [
                "preserved_elements_present: list of items from `preserved_elements` that are still preserved after the edit",
            ]
        )
    structural_fields_text = "\n".join(f"- {field}" for field in structural_fields)

    return dedent(
        f"""
        TASK: {task_id}

        USER PROMPT:
        {prompt}

        ASSERTIONS JSON:
        {json.dumps(assertions, indent=2)}
        {source_section}
        MODEL OUTPUT:
        ---
        {{model_output}}
        ---

        {"You will also receive three images for this edit task in this exact order: Image 1 is the original source diagram PNG, Image 2 is the reference target PNG, and Image 3 is the rendered PNG of the model output. Compare Image 3 against Image 2 while using Image 1 as the original baseline." if is_edit_task else ""}

        Evaluate this task with the same rubric used for every benchmark task.

        structural evidence:
        {structural_fields_text}
        - Do not compute the structural score yourself from intuition.
        - Report only the structural evidence requested above so the harness can compare it against the assertions JSON.

        semantics rubric:
        - `connections_correct`: 1 if the connections are made properly, else 0.
        - `text_inside_nodes_correct`: 1 if all text inside nodes, including multiline node text if any, is correctly present, else 0.
        - `text_centered_in_nodes`: 1 if labels or multiline text inside boxes/icons/nodes are visually centered within their components, else 0.
        - `layout_matches_prompt`: 1 if the overall layout/architecture follows the prompt strictly, else 0.
        - `labels_spelled_correct`: 1 if visible labels are spelled correctly with no obvious typos, truncation, or wrong wording, else 0.
        - `arrows_cleanly_aligned`: 1 if arrows are centered and visually aligned to the correct lanes, boxes, nodes, and targets, with arrowheads attaching cleanly where they should. If an arrow has a label, the label should sit a little above the arrow rather than inside the arrow line. Otherwise 0.

        Rules:
        - Use this exact rubric only. Do not invent a task-specific checklist.
        - Keep reason short and concrete.

        RESPOND WITH JSON ONLY:
        {{
          "structural_observations": {{
            "required_labels_present": [],
            "entity_count_observed": 0,
            "required_edges_present": []{', "required_edge_labels_present": []' if has_required_edge_labels else ''}{', "preserved_elements_present": []' if is_edit_task else ''}
          }},
          "semantics": {{
            "connections_correct": 0,
            "text_inside_nodes_correct": 0,
            "text_centered_in_nodes": 0,
            "layout_matches_prompt": 0,
            "labels_spelled_correct": 0,
            "arrows_cleanly_aligned": 0
          }},
          "reason": "string"
        }}
        """
    ).strip("\n")
