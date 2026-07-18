#!/usr/bin/env python3
"""
Full-run ASCII diagram generation for TermDraw-Bench tasks (the `run-model`
console script), via OpenRouter's synchronous chat-completions API.

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

from scripts.lib.openrouter_api import (
    chat_completion_with_retries,
    estimate_cost_usd,
    extract_chat_content,
    extract_usage,
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

# Per-model OpenRouter pricing defaults (USD per 1M tokens), keyed by the
# model's short name (the part after the last "/" in its OpenRouter model
# slug). Only used when --input-price-per-million/--output-price-per-million
# are not passed on the CLI; fully overridable. Source: openrouter.ai model
# pages (checked 2026-07-18).
MODEL_PRICING_DEFAULTS: dict[str, tuple[float, float]] = {
    "qwen3.7-plus": (0.32, 1.28),
    "minimax-m3": (0.30, 1.20),
    "kimi-k2.6": (0.66, 3.41),
}


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


def build_readable_final_prompt(system_prompt: str, user_content: str | list[dict[str, Any]]) -> str:
    """Build a human-readable stand-in for the generation request, for saving to ground_truth/final_prompt.txt.

    The real API call still sends user_content as-is (with the real inline
    base64 image for category 3 tasks); this just avoids dumping that raw
    base64 data URL into the saved record via json.dumps.
    """
    if isinstance(user_content, list):
        parts: list[str] = []
        for block in user_content:
            if block.get("type") == "text":
                parts.append(block["text"])
            elif block.get("type") == "image_url":
                parts.append("[image attached — see source.png in this folder]")
        user_text = "\n\n".join(parts)
    else:
        user_text = user_content
    return f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_text}"


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


def write_output_and_render_png(outputs_dir: Path, task_dir: Path, text: str, final_prompt: str = "") -> tuple[Path, Path]:
    """Write a task's generated ASCII text under outputs_dir (mirroring the tasks/ layout), render it to a PNG alongside it, and set up gval/ + ground_truth/ for judging.

    Rendering failures (e.g. a runaway/degenerate generation too large for
    Chromium to screenshot) are logged and swallowed rather than raised, so
    one bad task doesn't abort the rest of the batch — the .txt is still
    written either way.
    """
    import shutil

    target_dir = task_output_dir(outputs_dir, task_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{task_dir.name}.txt"
    png_path = target_dir / f"{task_dir.name}.png"
    output_path.write_text(text.strip() + "\n")
    try:
        render_ascii_file_to_png(output_path, png_path)
    except Exception as exc:
        line_count = text.count("\n") + 1
        print(
            f"WARNING: failed to render PNG for {task_dir.name} "
            f"({line_count} lines, {len(text)} chars — likely a degenerate/runaway generation): {exc}"
        )

    # ground_truth/  — reference files for the judge (per-task)
    gt_dir = target_dir / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)
    for src_name in ("reference.png", "prompt.txt", "assertions.json"):
        src = task_dir / src_name
        if src.exists():
            shutil.copy2(src, gt_dir / src_name)
    source_png = task_dir / "source.png"
    if source_png.exists():
        shutil.copy2(source_png, gt_dir / "source.png")
    if final_prompt:
        (gt_dir / "final_prompt.txt").write_text(final_prompt)

    # gval/  — ready for judge results (per-task)
    (target_dir / "gval").mkdir(parents=True, exist_ok=True)

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
    max_tokens: int | None,
    top_p: float | None = 0.95,
    input_price_per_million: float | None = None,
    output_price_per_million: float | None = None,
    generation_seed: int | None = None,
) -> None:
    """Generate ASCII diagrams for the selected tasks and write outputs + a manifest.json."""
    model_short_name = model_name.rstrip("/").rsplit("/", 1)[-1]
    outputs = Path(outputs_dir) / model_short_name
    outputs.mkdir(parents=True, exist_ok=True)

    if input_price_per_million is None and output_price_per_million is None:
        input_price_per_million, output_price_per_million = MODEL_PRICING_DEFAULTS.get(
            model_short_name, (None, None)
        )

    api_key = require_env("OPENROUTER_API_KEY")
    tasks = Path(tasks_dir)

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
        + " If you are about to output anything other than ASCII diagram text, stop and output only the diagram."
    )

    manifest = {
        "model": model_name,
        "reasoning_effort": reasoning_effort,
        "network_retries": network_retries,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "generation_seed": generation_seed,
        "tasks": [task_dir.name for task_dir in selected_task_dirs],
        "results": [],
    }

    written = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0
    cost_known = input_price_per_million is not None and output_price_per_million is not None
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
            max_tokens=max_tokens,
            top_p=top_p,
            seed=generation_seed,
            reasoning_effort=reasoning_effort,
            network_retries=network_retries,
            request_label=f"generation {task_id}",
        )
        text = extract_chat_content(response)
        usage = extract_usage(response)
        final_prompt = build_readable_final_prompt(system_prompt, user_content)
        output_path, png_path = write_output_and_render_png(outputs, task_dir, text, final_prompt)
        written += 1

        result: dict[str, Any] = {
            "task_id": task_id,
            "output_file": str(output_path),
            "png_file": str(png_path),
            "transport": "openrouter-chat-completions",
        }
        cost_note = ""
        if usage is not None:
            result["input_tokens"] = usage["prompt_tokens"]
            result["output_tokens"] = usage["completion_tokens"]
            result["total_tokens"] = usage["total_tokens"]
            total_input_tokens += usage["prompt_tokens"]
            total_output_tokens += usage["completion_tokens"]
            # Prefer OpenRouter's own reported per-request cost (provider-side
            # computed, not an estimate) over the MODEL_PRICING_DEFAULTS table.
            task_cost = usage.get("real_cost_usd")
            if task_cost is None:
                task_cost = estimate_cost_usd(
                    input_tokens=usage["prompt_tokens"],
                    output_tokens=usage["completion_tokens"],
                    input_price_per_million=input_price_per_million,
                    output_price_per_million=output_price_per_million,
                )
            if task_cost is not None:
                result["cost_usd"] = task_cost
                total_cost_usd += task_cost
                cost_known = True
                cost_note = f", cost=${task_cost:.4f}"
        manifest["results"].append(result)
        print(f"Done: {task_id}{cost_note}")

    manifest["total_input_tokens"] = total_input_tokens
    manifest["total_output_tokens"] = total_output_tokens
    if cost_known:
        manifest["total_cost_usd"] = total_cost_usd

    (outputs / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    cost_summary = f", total cost=${total_cost_usd:.4f}" if cost_known else ""
    print(f"Wrote {written} outputs to {outputs}{cost_summary}")


def main() -> None:
    """CLI entrypoint for `run-model`: parse args and run generation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="OpenRouter model slug, e.g. qwen/qwen3.7-plus")
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
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Local RNG seed for --sample-count task selection only. Not sent to the OpenRouter API — see --generation-seed for that.",
    )
    parser.add_argument(
        "--reasoning-effort",
        default="none",
        help="OpenRouter reasoning effort control for generation. Defaults to 'none'.",
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Cap on generated tokens per task, so a degenerate/repetition-looping generation can't grow unbounded. Pass 0 to disable (use the model's own default/max).",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.95,
        help="Nucleus sampling cutoff for generation. Defaults to 0.95; pass 0 to omit and use the model's own default.",
    )
    parser.add_argument(
        "--generation-seed",
        type=int,
        help="OpenRouter `seed` param for best-effort deterministic sampling on the generation call. Omitted by default (provider's own behavior). Not a hard reproducibility guarantee -- provider-dependent.",
    )
    parser.add_argument(
        "--input-price-per-million",
        type=float,
        help="USD price per 1M input tokens for the generation model, to compute cost_usd if OpenRouter doesn't report its own usage.cost. Known models (e.g. qwen3.7-plus) have built-in defaults; this flag overrides.",
    )
    parser.add_argument(
        "--output-price-per-million",
        type=float,
        help="USD price per 1M output tokens for the generation model, to compute cost_usd if OpenRouter doesn't report its own usage.cost. Known models (e.g. qwen3.7-plus) have built-in defaults; this flag overrides.",
    )
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
        args.max_tokens or None,
        args.top_p or None,
        args.input_price_per_million,
        args.output_price_per_million,
        args.generation_seed,
    )


if __name__ == "__main__":
    main()
