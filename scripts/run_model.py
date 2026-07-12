#!/usr/bin/env python3
"""
Run Fireworks batch inference on all TermDraw-Bench tasks and save outputs.

Category 3 tasks are sent as multimodal requests using `source.png`.
All other categories are sent as text-only chat completion requests.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lib.fireworks_api import (
    create_batch_job,
    create_dataset,
    create_session,
    download_signed_files,
    extract_batch_content,
    get_dataset_download_urls,
    iter_task_dirs,
    read_jsonl,
    require_env,
    slugify,
    truncate_display_name,
    upload_dataset_file,
    wait_for_batch_job,
)


SYSTEM_PROMPT = (
    "You are a technical documentation assistant. "
    "Generate correct, well-formed ASCII diagrams using only standard "
    "ASCII characters: + - | > < ^ v / \\ . "
    "Return only the final diagram. No markdown fences. No explanation. "
    "Do not reveal reasoning or thinking. Start directly with ASCII."
)


def timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def encode_image_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def build_user_content(task_id: str, task_dir: Path, oneshot_dir: Path) -> str | list[dict[str, Any]]:
    category = task_id.split(".", 1)[0]
    prompt_text = (task_dir / "prompt.txt").read_text().strip()
    oneshot_file = Path(oneshot_dir) / f"c{category}_example.txt"
    sections: list[str] = []
    if oneshot_file.exists():
        sections.append("Example target style:\n" + oneshot_file.read_text().strip())
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


def build_rows(task_dirs: list[Path], oneshot_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task_dir in task_dirs:
        task_id = task_dir.name
        rows.append(
            {
                "custom_id": task_id,
                "body": {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": build_user_content(task_id, task_dir, oneshot_dir),
                        },
                    ]
                },
            }
        )
    if not rows:
        raise RuntimeError("No task requests were generated.")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def run(
    model_name: str,
    tasks_dir: str,
    outputs_dir: str,
    oneshot_dir: str,
    account_id: str | None,
    job_id: str | None,
    input_dataset_id: str | None,
    output_dataset_id: str | None,
    poll_interval: float,
    max_tokens: int,
    temperature: float,
    top_p: float,
    network_retries: int,
    task_ids: list[str] | None,
    sample_count: int | None,
    seed: int,
    reasoning_effort: str,
) -> None:
    api_key = require_env("FIREWORKS_API_KEY")
    account_id = account_id or require_env("FIREWORKS_ACCOUNT_ID")
    tasks = Path(tasks_dir)
    outputs = Path(outputs_dir)
    oneshot = Path(oneshot_dir)
    outputs.mkdir(parents=True, exist_ok=True)

    run_slug = slugify(outputs.name or "model")
    stamp = timestamp()
    input_dataset_id = input_dataset_id or f"termdraw-{run_slug}-input-{stamp}"
    output_dataset_id = output_dataset_id or f"termdraw-{run_slug}-output-{stamp}"
    job_id = job_id or f"termdraw-{run_slug}-gen-{stamp}"

    metadata_dir = outputs / "_fireworks_batch" / job_id
    metadata_dir.mkdir(parents=True, exist_ok=True)
    input_jsonl = metadata_dir / "requests.jsonl"
    selected_task_dirs = select_task_dirs(
        tasks,
        task_ids=task_ids,
        sample_count=sample_count,
        seed=seed,
    )
    rows = build_rows(selected_task_dirs, oneshot)
    write_jsonl(input_jsonl, rows)

    session = create_session(api_key)
    create_dataset(
        session,
        account_id,
        input_dataset_id,
        truncate_display_name(f"TermDraw input {job_id}"),
        example_count=len(rows),
        max_retries=network_retries,
    )
    upload_response = upload_dataset_file(
        session,
        account_id,
        input_dataset_id,
        input_jsonl,
        max_retries=network_retries,
    )
    job = create_batch_job(
        session,
        account_id,
        job_id=job_id,
        model=model_name,
        input_dataset_id=input_dataset_id,
        output_dataset_id=output_dataset_id,
        inference_parameters={
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topP": top_p,
            "extraBody": json.dumps({"reasoning_effort": reasoning_effort}),
        },
        display_name=truncate_display_name(f"TermDraw generation {job_id}"),
        max_retries=network_retries,
    )
    final_job = wait_for_batch_job(
        session,
        account_id,
        job_id,
        poll_interval=poll_interval,
        max_retries=network_retries,
    )
    state = (final_job.get("state") or "").replace("JOB_STATE_", "")
    if state != "COMPLETED":
        raise RuntimeError(f"Generation batch job ended in state {state}")

    downloaded = download_signed_files(
        get_dataset_download_urls(
            session,
            account_id,
            output_dataset_id,
            max_retries=network_retries,
        ),
        metadata_dir / "downloaded",
        max_retries=network_retries,
    )

    written = 0
    for file_path in downloaded:
        if file_path.suffix != ".jsonl":
            continue
        for row in read_jsonl(file_path):
            task_id = row.get("custom_id")
            if not task_id:
                continue
            text = extract_batch_content(row)
            (outputs / f"{task_id}.txt").write_text(text.strip() + "\n")
            written += 1
            print(f"Done: {task_id}")

    if not written:
        raise RuntimeError("No task outputs were parsed from Fireworks batch results.")

    manifest = {
        "model": model_name,
        "account_id": account_id,
        "job_id": job_id,
        "input_dataset_id": input_dataset_id,
        "output_dataset_id": output_dataset_id,
        "request_count": len(rows),
        "upload_response": upload_response,
        "job": job,
        "final_job": final_job,
        "downloaded_files": [str(path) for path in downloaded],
        "written_outputs": written,
    }
    (metadata_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {written} outputs to {outputs}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Fireworks model path")
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--oneshot", default="oneshot")
    parser.add_argument("--account-id")
    parser.add_argument("--job-id")
    parser.add_argument("--input-dataset-id")
    parser.add_argument("--output-dataset-id")
    parser.add_argument("--poll-interval", type=float, default=10.0)
    parser.add_argument("--max-tokens", type=int, default=768)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
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
    args = parser.parse_args()
    run(
        args.model,
        args.tasks,
        args.outputs,
        args.oneshot,
        args.account_id,
        args.job_id,
        args.input_dataset_id,
        args.output_dataset_id,
        args.poll_interval,
        args.max_tokens,
        args.temperature,
        args.top_p,
        args.network_retries,
        [item.strip() for item in args.task_ids.split(",") if item.strip()]
        if args.task_ids
        else None,
        args.sample_count,
        args.seed,
        args.reasoning_effort,
    )
