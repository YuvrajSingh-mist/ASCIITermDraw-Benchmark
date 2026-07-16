#!/usr/bin/env python3
"""
Full-run ASCII diagram generation for TermDraw-Bench tasks (the `run-model`
console script), via Fireworks' synchronous chat-completions API.

Category 3 tasks are sent as multimodal requests using `source.png`.
All other categories are sent as text-only chat completion requests.
`smoke_generate.py` reuses `SYSTEM_PROMPT`, `build_user_content`,
`select_task_dirs`, and `write_output_and_render_png` from this module.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import random
from pathlib import Path
from typing import Any

from scripts.lib.fireworks_api import (
    chat_completion_with_retries,
    extract_chat_content,
    iter_task_dirs,
    require_env,
    task_output_dir,
)
from scripts.rendered.render import render as render_ascii_file_to_png


SYSTEM_PROMPT = (
    "You are a technical documentation assistant. "
    "Generate correct, well-formed ASCII diagrams using only standard "
    "ASCII characters: + - | > < ^ v / \\ ( ) = * . "
    "Return only the final diagram. No markdown fences. No explanation. "
    "Do not reveal reasoning or thinking. Start directly with ASCII."
)


def encode_image_data_url(image_path: Path) -> str:
    """Base64-encode an image file into a data: URL for inline embedding in a chat message."""
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def build_user_content(task_id: str, task_dir: Path) -> str | list[dict[str, Any]]:
    """Build the user message for a task: plain prompt text, or (for category 3 edits) prompt text plus the attached source.png."""
    category = task_id.split(".", 1)[0]
    prompt_text = (task_dir / "prompt.txt").read_text().strip()
    sections: list[str] = []
    if category == "3":
        sections.append(
            "The source diagram is attached as an image. "
            "Apply the requested edit and return only the final ASCII diagram."
        )
    sections.append("Task:\n" + prompt_text)
    sections.append("Output only the final ASCII diagram.")
    prompt = "\n\n".join(sections)

    if category != "3":
        return prompt

    source_png = task_dir / "source.png"
    if not source_png.exists():
        raise RuntimeError(
            f"Category 3 task {task_id} is missing {source_png}. "
            "Render PNG assets before running model inference."
        )
    return [
        {"type": "text", "text": prompt},
        {
            "type": "image_url",
            "image_url": {"url": encode_image_data_url(source_png)},
        },
    ]


def select_task_dirs(
    tasks_dir: Path,
    *,
    task_ids: list[str] | None,
    sample_count: int | None,
    seed: int,
) -> list[Path]:
    """Pick which task directories to run: optionally filter to explicit task_ids, then optionally random-sample sample_count of them."""
    task_dirs = [task_dir for task_dir in iter_task_dirs(tasks_dir) if (task_dir / "prompt.txt").exists()]
    if task_ids:
        selected = [task_dir for task_dir in task_dirs if task_dir.name in set(task_ids)]
        missing = sorted(set(task_ids) - {task_dir.name for task_dir in selected})
        if missing:
            raise RuntimeError(f"Unknown task ids requested: {', '.join(missing)}")
        task_dirs = selected

    if sample_count is not None:
        if sample_count <= 0:
            raise RuntimeError("--sample-count must be positive.")
        if sample_count < len(task_dirs):
            rng = random.Random(seed)
            task_dirs = sorted(
                rng.sample(task_dirs, sample_count),
                key=lambda path: tuple(int(part) for part in path.name.split(".")),
            )
    return task_dirs


def write_output_and_render_png(outputs_dir: Path, task_dir: Path, text: str) -> tuple[Path, Path]:
    """Write a task's generated ASCII text under outputs_dir (mirroring the tasks/ layout) and render it to a PNG alongside it."""
    target_dir = task_output_dir(outputs_dir, task_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{task_dir.name}.txt"
    png_path = target_dir / f"{task_dir.name}.png"
    output_path.write_text(text.strip() + "\n")
    render_ascii_file_to_png(output_path, png_path)
    return output_path, png_path


def run(
    model_name: str,
    tasks_dir: str,
    outputs_dir: str,
    network_retries: int,
    task_ids: list[str] | None,
    sample_count: int | None,
    seed: int,
    reasoning_effort: str,
    temperature: float,
) -> None:
    """Generate ASCII diagrams for the selected tasks and write outputs + a manifest.json."""
    api_key = require_env("FIREWORKS_API_KEY")
    tasks = Path(tasks_dir)
    outputs = Path(outputs_dir)
    outputs.mkdir(parents=True, exist_ok=True)

    selected_task_dirs = select_task_dirs(
        tasks,
        task_ids=task_ids,
        sample_count=sample_count,
        seed=seed,
    )
    if not selected_task_dirs:
        raise RuntimeError("No tasks selected for generation.")

    system_prompt = (
        SYSTEM_PROMPT
        + " Thinking/reasoning is disabled for this request. "
        + "If you are about to output anything other than ASCII diagram text, stop and output only the diagram."
    )

    manifest = {
        "model": model_name,
        "reasoning_effort": reasoning_effort,
        "network_retries": network_retries,
        "tasks": [task_dir.name for task_dir in selected_task_dirs],
        "results": [],
    }

    written = 0
    for task_dir in selected_task_dirs:
        task_id = task_dir.name
        user_content = build_user_content(task_id, task_dir)
        response = chat_completion_with_retries(
            api_key,
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
            reasoning_effort=reasoning_effort,
            network_retries=network_retries,
            request_label=f"generation {task_id}",
        )
        text = extract_chat_content(response)
        output_path, png_path = write_output_and_render_png(outputs, task_dir, text)
        written += 1
        print(f"Done: {task_id}")

        manifest["results"].append(
            {
                "task_id": task_id,
                "output_file": str(output_path),
                "png_file": str(png_path),
                "transport": "fireworks-chat-completions",
            }
        )

    (outputs / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {written} outputs to {outputs}")


def main() -> None:
    """CLI entrypoint for `run-model`: parse args and run generation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Fireworks model path")
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument(
        "--network-retries",
        type=int,
        default=5,
        help="Retry count for network, rate-limit, and transient server failures only.",
    )
    parser.add_argument(
        "--task-ids",
        help="Comma-separated task ids to run, for example 1.1,2.4,3.7",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        help="Randomly sample this many tasks from the selected task set.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--reasoning-effort",
        default="none",
        help="Fireworks reasoning control for generation. Defaults to 'none'.",
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()
    run(
        args.model,
        args.tasks,
        args.outputs,
        args.network_retries,
        [item.strip() for item in args.task_ids.split(",") if item.strip()]
        if args.task_ids
        else None,
        args.sample_count,
        args.seed,
        args.reasoning_effort,
        args.temperature,
    )


if __name__ == "__main__":
    main()
