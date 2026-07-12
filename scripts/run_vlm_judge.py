#!/usr/bin/env python3
"""
Run Fireworks batch judging for TermDraw-Bench using structured JSON output.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel, ConfigDict
except ModuleNotFoundError as _PYDANTIC_ERROR:
    BaseModel = object

    def ConfigDict(**_: Any) -> dict[str, Any]:
        return {}
else:
    _PYDANTIC_ERROR = None

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


class JudgeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scores: dict[str, float]
    total: float
    passed: bool
    reason: str

SYSTEM_PROMPT = (
    "You are a strict ASCII-diagram benchmark judge. "
    "Return JSON only. Score each checklist item as 0 or 1 in `scores`, "
    "set `total` to the sum of those checklist scores, set `passed` to true "
    "only when the diagram satisfies the task, and keep `reason` concise."
)


def timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def build_rows(tasks_dir: Path, outputs_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task_dir in iter_task_dirs(tasks_dir):
        task_id = task_dir.name
        output_file = outputs_dir / f"{task_id}.txt"
        judge_file = task_dir / "vlm_judge_prompt.txt"
        if not output_file.exists():
            print(f"Skipping {task_id}: missing model output")
            continue
        prompt = judge_file.read_text().replace(
            "{model_output}",
            output_file.read_text().strip(),
        )
        prompt += (
            "\n\nReturn JSON that matches the required schema exactly. "
            "Use the boolean field name `passed` instead of `pass`."
        )
        rows.append(
            {
                "custom_id": task_id,
                "body": {
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ]
                },
            }
        )
    if not rows:
        raise RuntimeError("No judge requests were generated.")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def parse_structured_content(content: str) -> JudgeResult:
    try:
        return JudgeResult.model_validate_json(content)
    except Exception as exc:
        raise RuntimeError(f"Judge returned invalid JSON: {content}") from exc


def normalize_l2_score(payload: JudgeResult) -> float:
    values = list(payload.scores.values())
    if values:
        return sum(values) / len(values)
    if 0.0 <= payload.total <= 1.0:
        return payload.total
    return 0.0


def load_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def save_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def merge_results(
    results_path: Path,
    tasks_dir: Path,
    judged: dict[str, JudgeResult],
) -> None:
    existing = load_csv_rows(results_path)
    rows_by_task = {row["task_id"]: row for row in existing if row.get("task_id")}

    if not rows_by_task:
        for task_dir in iter_task_dirs(tasks_dir):
            rows_by_task[task_dir.name] = {"task_id": task_dir.name}

    for task_id, payload in judged.items():
        row = rows_by_task.setdefault(task_id, {"task_id": task_id})
        l2_score = normalize_l2_score(payload)
        row["L2_score"] = f"{l2_score:.4f}"
        row["L2_passed"] = str(payload.passed).lower()
        row["L2_reason"] = payload.reason
        row["L2_total_raw"] = str(payload.total)
        if row.get("L1_total"):
            try:
                l1 = float(row["L1_total"])
                row["final_score"] = f"{(l1 + l2_score) / 2:.4f}"
            except ValueError:
                row["final_score"] = ""
        else:
            row["final_score"] = f"{l2_score:.4f}"

    merged_rows = [rows_by_task[task_dir.name] for task_dir in iter_task_dirs(tasks_dir)]
    save_csv_rows(results_path, merged_rows)


def run(
    *,
    model: str,
    tasks_dir: str,
    outputs_dir: str,
    results_path: str,
    account_id: str | None,
    job_id: str | None,
    input_dataset_id: str | None,
    output_dataset_id: str | None,
    poll_interval: float,
    max_tokens: int,
    network_retries: int,
) -> None:
    if _PYDANTIC_ERROR is not None:
        raise RuntimeError(
            "Missing Python dependency `pydantic`. "
            "Install it with `.venv/bin/python -m pip install -r requirements.txt`."
        ) from _PYDANTIC_ERROR

    api_key = require_env("FIREWORKS_API_KEY")
    account_id = account_id or require_env("FIREWORKS_ACCOUNT_ID")
    tasks = Path(tasks_dir)
    outputs = Path(outputs_dir)
    results = Path(results_path)

    run_slug = slugify(outputs.name or "judge")
    stamp = timestamp()
    input_dataset_id = input_dataset_id or f"termdraw-{run_slug}-judge-input-{stamp}"
    output_dataset_id = output_dataset_id or f"termdraw-{run_slug}-judge-output-{stamp}"
    job_id = job_id or f"termdraw-{run_slug}-judge-{stamp}"

    metadata_dir = outputs / "_fireworks_judge" / job_id
    metadata_dir.mkdir(parents=True, exist_ok=True)
    input_jsonl = metadata_dir / "judge_requests.jsonl"
    rows = build_rows(tasks, outputs)
    write_jsonl(input_jsonl, rows)

    session = create_session(api_key)
    create_dataset(
        session,
        account_id,
        input_dataset_id,
        truncate_display_name(f"TermDraw judge input {job_id}"),
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
    inference_parameters = {
        "maxTokens": max_tokens,
        "temperature": 0,
        "topP": 1,
        "extraBody": json.dumps(
            {
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "TermDrawJudgeResult",
                        "schema": JudgeResult.model_json_schema(),
                    },
                }
            }
        ),
    }
    job = create_batch_job(
        session,
        account_id,
        job_id=job_id,
        model=model,
        input_dataset_id=input_dataset_id,
        output_dataset_id=output_dataset_id,
        inference_parameters=inference_parameters,
        display_name=truncate_display_name(f"TermDraw judge {job_id}"),
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
        raise RuntimeError(f"Judge batch job ended in state {state}")

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

    judged: dict[str, JudgeResult] = {}
    json_dir = outputs / "judge_json"
    json_dir.mkdir(parents=True, exist_ok=True)
    for file_path in downloaded:
        if file_path.suffix != ".jsonl":
            continue
        for row in read_jsonl(file_path):
            task_id = row.get("custom_id")
            if not task_id:
                continue
            payload = parse_structured_content(extract_batch_content(row))
            judged[task_id] = payload
            (json_dir / f"{task_id}.json").write_text(
                payload.model_dump_json(indent=2) + "\n"
            )

    if not judged:
        raise RuntimeError("No judge outputs were parsed from Fireworks batch results.")

    merge_results(results, tasks, judged)
    manifest = {
        "model": model,
        "account_id": account_id,
        "job_id": job_id,
        "input_dataset_id": input_dataset_id,
        "output_dataset_id": output_dataset_id,
        "request_count": len(rows),
        "upload_response": upload_response,
        "job": job,
        "final_job": final_job,
        "downloaded_files": [str(path) for path in downloaded],
        "results_csv": str(results),
    }
    (metadata_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Judged {len(judged)} tasks and updated {results}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Fireworks model path")
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--account-id")
    parser.add_argument("--job-id")
    parser.add_argument("--input-dataset-id")
    parser.add_argument("--output-dataset-id")
    parser.add_argument("--poll-interval", type=float, default=10.0)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument(
        "--network-retries",
        type=int,
        default=5,
        help="Retry count for network, rate-limit, and transient server failures only.",
    )
    args = parser.parse_args()
    run(
        model=args.model,
        tasks_dir=args.tasks,
        outputs_dir=args.outputs,
        results_path=args.results,
        account_id=args.account_id,
        job_id=args.job_id,
        input_dataset_id=args.input_dataset_id,
        output_dataset_id=args.output_dataset_id,
        poll_interval=args.poll_interval,
        max_tokens=args.max_tokens,
        network_retries=args.network_retries,
    )
