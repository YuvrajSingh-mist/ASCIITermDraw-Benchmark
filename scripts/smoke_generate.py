#!/usr/bin/env python3
"""
Run a small synchronous Fireworks smoke test against TermDraw-Bench tasks.

This is useful for quickly checking model behavior before paying the batch-job
latency cost. It uses the same prompt construction as `scripts/run_model.py`
and disables reasoning by default.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.lib.fireworks_api import (
    chat_completion_with_retries,
    extract_chat_content,
    require_env,
)
from scripts.run_model import (
    SYSTEM_PROMPT,
    build_user_content,
    select_task_dirs,
    write_output_and_render_png,
)


def run(
    *,
    model: str,
    tasks_dir: str,
    oneshot_dir: str,
    outputs_dir: str,
    task_ids: list[str] | None,
    sample_count: int | None,
    seed: int,
    max_tokens: int,
    temperature: float,
    top_p: float,
    reasoning_effort: str,
    network_retries: int,
) -> None:
    api_key = require_env("FIREWORKS_API_KEY")

    tasks = Path(tasks_dir)
    oneshot = Path(oneshot_dir)
    outputs = Path(outputs_dir)
    outputs.mkdir(parents=True, exist_ok=True)

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
        + " Thinking/reasoning is disabled for this request. "
        + "If you are about to output anything other than ASCII diagram text, stop and output only the diagram."
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
        user_content = build_user_content(task_id, task_dir, oneshot)
        response = chat_completion_with_retries(
            api_key,
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            reasoning_effort=reasoning_effort,
            network_retries=network_retries,
            request_label=f"smoke test {task_id}",
        )
        text = extract_chat_content(response)

        output_path, png_path = write_output_and_render_png(outputs, task_id, text)
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
                "transport": "fireworks-chat-completions",
            }
        )

    (outputs / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(selected_task_dirs)} smoke-test outputs to {outputs}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Fireworks model path")
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--oneshot", default="oneshot")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--task-ids", help="Comma-separated task ids, for example 1.4,2.6,4.3")
    parser.add_argument("--sample-count", type=int, help="Randomly sample this many tasks.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-tokens", type=int, default=768)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--reasoning-effort", default="none")
    parser.add_argument("--network-retries", type=int, default=5)
    args = parser.parse_args()

    run(
        model=args.model,
        tasks_dir=args.tasks,
        oneshot_dir=args.oneshot,
        outputs_dir=args.outputs,
        task_ids=[item.strip() for item in args.task_ids.split(",") if item.strip()]
        if args.task_ids
        else None,
        sample_count=args.sample_count,
        seed=args.seed,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        reasoning_effort=args.reasoning_effort,
        network_retries=args.network_retries,
    )


if __name__ == "__main__":
    main()
