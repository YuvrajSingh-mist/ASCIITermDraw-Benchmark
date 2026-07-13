from __future__ import annotations

import json
from textwrap import dedent


COMMON_PROMPT_SUFFIX = (
    " Return only the final ASCII diagram in plain text. "
    "Do not include markdown fences, explanations, or any extra text."
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


def finalize_task_prompt(task_id: str, prompt: str) -> str:
    prompt = prompt.strip()
    suffix = COMMON_PROMPT_SUFFIX
    if task_id.startswith("3."):
        suffix = EDITING_PROMPT_SUFFIX + COMMON_PROMPT_SUFFIX
    if prompt.endswith(suffix.strip()):
        return prompt
    joiner = "\n" if "\n" in prompt else ""
    return prompt + joiner + suffix.lstrip()


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

    structural_fields = [
        "required_labels_present: list of labels from `required_labels` that are clearly present in the model output",
        "entity_count_observed: integer count of entities/nodes/boxes observed in the model output",
        "required_edges_present: list of edges from `required_edges` that are clearly present in the model output, using the same `{from, to}` strings as the assertions JSON",
    ]
    if is_edit_task:
        structural_fields.extend(
            [
                "required_edge_labels_present: list of labels from `required_edge_labels` that are clearly present",
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
        - `layout_matches_prompt`: 1 if the layout follows the prompt strictly, else 0.

        Rules:
        - Use this exact rubric only. Do not invent a task-specific checklist.
        - Keep reason short and concrete.

        RESPOND WITH JSON ONLY:
        {{
          "structural_observations": {{
            "required_labels_present": [],
            "entity_count_observed": 0,
            "required_edges_present": []{', "required_edge_labels_present": [], "preserved_elements_present": []' if is_edit_task else ''}
          }},
          "semantics": {{
            "connections_correct": 0,
            "text_inside_nodes_correct": 0,
            "layout_matches_prompt": 0
          }},
          "reason": "string"
        }}
        """
    ).strip("\n")
