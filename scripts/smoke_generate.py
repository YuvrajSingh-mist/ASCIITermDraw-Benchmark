#!/usr/bin/env python3
"""
Quick synchronous Together AI smoke test against a sample of TermDraw-Bench
tasks (the `smoke` console script) — useful for a fast sanity check before a
full `run-model` run. Shares prompt construction and output layout with
`scripts/run_model.py`; reasoning is disabled by default.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.lib.together_api import (
    chat_completion_with_retries,
    extract_chat_content,
    require_env,
)
from scripts.run_model import (
    SYSTEM_PROMPT,
    build_readable_final_prompt,
    build_user_content,
    select_task_dirs,
    write_output_and_render_png,
)


def run(
    *,
    model: str,
    tasks_dir: str,
    outputs_dir: str,
    task_ids: list[str] | None,
    sample_count: int | None,
    seed: int,
    temperature: float,
    max_tokens: int | None,
    top_p: float | None,
    reasoning_effort: str,
    network_retries: int,
) -> None:
    """Generate ASCII diagrams for a sample of tasks, print each result, and write outputs + a manifest.json."""
    outputs = Path(outputs_dir) / model.rstrip("/").rsplit("/", 1)[-1].lower()
    outputs.mkdir(parents=True, exist_ok=True)

    api_key = require_env("TOGETHER_API_KEY")
    tasks = Path(tasks_dir)

    selected_task_dirs = select_task_dirs(
        tasks,
        task_ids=task_ids,
        sample_count=sample_count,
        seed=seed,
    )
    if not selected_task_dirs:
        raise RuntimeError("No tasks selected for smoke test.")

    system_prompt = (
        SYSTEM_PROMPT
        + " If you are about to output anything other than ASCII diagram text, stop and output only the diagram."
    )

    manifest = {
        "model": model,
        "reasoning_effort": reasoning_effort,
        "network_retries": network_retries,
        "tasks": [task_dir.name for task_dir in selected_task_dirs],
        "results": [],
    }

    for task_dir in selected_task_dirs:
        task_id = task_dir.name
        user_content = build_user_content(task_id, task_dir)
        response = chat_completion_with_retries(
            api_key,
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            reasoning_effort=reasoning_effort,
            network_retries=network_retries,
            request_label=f"smoke test {task_id}",
        )
        text = extract_chat_content(response)
        final_prompt = build_readable_final_prompt(system_prompt, user_content)

        output_path, png_path = write_output_and_render_png(outputs, task_dir, text, final_prompt)
        preview = text[:300].replace("\n", "\\n")
        print(f"=== {task_id} ===")
        print(text)
        print()

        manifest["results"].append(
            {
                "task_id": task_id,
                "output_file": str(output_path),
                "png_file": str(png_path),
                "preview": preview,
                "transport": "together-chat-completions",
            }
        )

    (outputs / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(selected_task_dirs)} smoke-test outputs to {outputs}")


def main() -> None:
    """CLI entrypoint for `smoke`: parse args and run a sampled generation pass."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Together AI model slug, e.g. Qwen/Qwen3.7-Plus")
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--task-ids", help="Comma-separated task ids, for example 1.4,2.6,4.3")
    parser.add_argument("--sample-count", type=int, help="Randomly sample this many tasks.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Cap on generated tokens per task. Pass 0 to disable (use the model's own default/max) -- without a cap, insufficient account credit for the model's max output can cause an HTTP 402.",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.95,
        help="Nucleus sampling cutoff for generation. Defaults to 0.95; pass 0 to omit and use the model's own default.",
    )
    parser.add_argument("--reasoning-effort", default="none")
    parser.add_argument("--network-retries", type=int, default=5)
    args = parser.parse_args()

    run(
        model=args.model,
        tasks_dir=args.tasks,
        outputs_dir=args.outputs,
        task_ids=[item.strip() for item in args.task_ids.split(",") if item.strip()]
        if args.task_ids
        else None,
        sample_count=args.sample_count,
        seed=args.seed,
        temperature=args.temperature,
        max_tokens=args.max_tokens or None,
        top_p=args.top_p or None,
        reasoning_effort=args.reasoning_effort,
        network_retries=args.network_retries,
    )


if __name__ == "__main__":
    main()
