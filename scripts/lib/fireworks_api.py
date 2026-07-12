#!/usr/bin/env python3
"""Shared Fireworks Batch API helpers for TermDraw-Bench."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    import requests


API_ROOT = "https://api.fireworks.ai"
TERMINAL_JOB_STATES = {"COMPLETED", "FAILED", "EXPIRED"}
TASK_ID_RE = re.compile(r"^\d+\.\d+$")
RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
TASK_CATEGORY_DIRS = {
    "1": "box-layout-basics",
    "2": "network-topology-diagrams",
    "3": "diagram-editing",
    "4": "software-architecture-diagrams",
}
ROOT = Path(__file__).resolve().parents[2]
ENV_FILES = (ROOT / ".env.local", ROOT / ".env")


def load_local_env() -> None:
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


load_local_env()


def _requests_module():
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing Python dependency `requests`. "
            "Install it with `.venv/bin/python -m pip install -r requirements.txt`."
        ) from exc
    return requests


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _retry_sleep_seconds(response=None, attempt: int = 0) -> float:
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
    return min(30.0, 1.5 * (2 ** attempt))


def _request_with_retries(
    session,
    method: str,
    url: str,
    *,
    max_retries: int,
    timeout: int | float,
    **kwargs: Any,
):
    requests = _requests_module()
    last_error = None
    for attempt in range(max_retries):
        try:
            response = session.request(method, url, timeout=timeout, **kwargs)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as exc:
            last_error = exc
            if attempt == max_retries - 1:
                break
            delay = _retry_sleep_seconds(attempt=attempt)
            print(
                f"Retrying {method} {urlparse(url).path} after transport failure "
                f"({attempt + 1}/{max_retries}, sleep={delay:.1f}s): {exc}"
            )
            time.sleep(delay)
            continue

        if response.status_code in RETRYABLE_STATUS_CODES and attempt < max_retries - 1:
            delay = _retry_sleep_seconds(response=response, attempt=attempt)
            print(
                f"Retrying {method} {urlparse(url).path} after HTTP "
                f"{response.status_code} ({attempt + 1}/{max_retries}, sleep={delay:.1f}s)"
            )
            time.sleep(delay)
            continue

        return response

    raise RuntimeError(
        f"Fireworks API {method} {url} failed after {max_retries} attempts: {last_error}"
    ) from last_error


def create_session(api_key: str) -> requests.Session:
    requests = _requests_module()
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    return session


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    max_retries: int = 5,
    **kwargs: Any,
) -> dict[str, Any]:
    response = _request_with_retries(
        session,
        method,
        url,
        max_retries=max_retries,
        timeout=120,
        **kwargs,
    )
    if not response.ok:
        snippet = response.text[:1000]
        raise RuntimeError(
            f"Fireworks API {method} {url} failed with "
            f"{response.status_code}: {snippet}"
        )
    if not response.content:
        return {}
    return response.json()


class CurlHTTPError(RuntimeError):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"HTTP {status_code}: {body[:1000]}")
        self.status_code = status_code
        self.body = body


def _curl_json_request(
    api_key: str,
    *,
    url: str,
    payload: dict[str, Any],
    timeout: int | float,
) -> dict[str, Any]:
    curl = shutil.which("curl")
    if not curl:
        raise RuntimeError("Missing required system dependency: curl")
    result = subprocess.run(
        [
            curl,
            "-sS",
            "-X",
            "POST",
            url,
            "-H",
            f"Authorization: Bearer {api_key}",
            "-H",
            "Content-Type: application/json",
            "-H",
            "Accept: application/json",
            "-H",
            "User-Agent: TermDraw-Bench/1.0",
            "-d",
            json.dumps(payload),
            "-w",
            "\n%{http_code}",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "curl request failed")
    body, _, status_text = result.stdout.rpartition("\n")
    status_code = int(status_text.strip() or "0")
    if status_code >= 400:
        raise CurlHTTPError(status_code, body.strip())
    return json.loads(body)


def chat_completion_with_retries(
    api_key: str,
    *,
    model: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
    temperature: float,
    top_p: float,
    reasoning_effort: str,
    network_retries: int,
    timeout: int | float = 90,
    request_label: str = "chat completion",
) -> dict[str, Any]:
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "reasoning_effort": reasoning_effort,
        "messages": messages,
    }
    last_error = None
    for attempt in range(network_retries):
        try:
            return _curl_json_request(
                api_key,
                url=f"{API_ROOT}/inference/v1/chat/completions",
                payload=payload,
                timeout=timeout,
            )
        except CurlHTTPError as exc:
            last_error = exc
            if exc.status_code in RETRYABLE_STATUS_CODES and attempt < network_retries - 1:
                delay = _retry_sleep_seconds(attempt=attempt)
                print(
                    f"Retrying {request_label} after HTTP {exc.status_code} "
                    f"({attempt + 1}/{network_retries}, sleep={delay:.1f}s)"
                )
                time.sleep(delay)
                continue
            raise RuntimeError(
                f"Fireworks {request_label} failed with HTTP {exc.status_code}: "
                f"{exc.body[:1500]}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            last_error = exc
            if attempt == network_retries - 1:
                raise
            delay = _retry_sleep_seconds(attempt=attempt)
            print(
                f"Retrying {request_label} after timeout "
                f"({attempt + 1}/{network_retries}, sleep={delay:.1f}s): {exc}"
            )
            time.sleep(delay)
        except RuntimeError as exc:
            last_error = exc
            if attempt == network_retries - 1:
                raise
            delay = _retry_sleep_seconds(attempt=attempt)
            print(
                f"Retrying {request_label} after transport failure "
                f"({attempt + 1}/{network_retries}, sleep={delay:.1f}s): {exc}"
            )
            time.sleep(delay)
    raise RuntimeError(f"No response received for {request_label}: {last_error}")


def dataset_name(account_id: str, dataset_id: str) -> str:
    if dataset_id.startswith("accounts/"):
        return dataset_id
    return f"accounts/{account_id}/datasets/{dataset_id}"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "run"


def truncate_display_name(value: str, limit: int = 63) -> str:
    return value[:limit]


def task_sort_key(task_id: str) -> tuple[int, float]:
    category, remainder = task_id.split(".", 1)
    return int(category), float(f"{category}.{remainder}")


def iter_task_dirs(tasks_dir: Path) -> list[Path]:
    return sorted(
        [
            path
            for path in tasks_dir.rglob("*")
            if path.is_dir() and TASK_ID_RE.fullmatch(path.name)
        ],
        key=lambda path: task_sort_key(path.name),
    )


def task_dir_path(tasks_dir: Path, task_id: str) -> Path:
    category = task_id.split(".", 1)[0]
    return tasks_dir / TASK_CATEGORY_DIRS.get(category, category) / task_id


def create_dataset(
    session: requests.Session,
    account_id: str,
    dataset_id: str,
    display_name: str,
    *,
    example_count: int,
    max_retries: int = 5,
) -> dict[str, Any]:
    url = f"{API_ROOT}/v1/accounts/{account_id}/datasets"
    payload = {
        "datasetId": dataset_id,
        "dataset": {
            "displayName": display_name,
            "exampleCount": str(example_count),
            "userUploaded": {},
        },
    }
    response = _request_with_retries(
        session,
        "POST",
        url,
        max_retries=max_retries,
        timeout=120,
        json=payload,
    )
    if response.status_code == 409:
        return {"datasetId": dataset_id, "already_exists": True}
    if not response.ok:
        snippet = response.text[:1000]
        raise RuntimeError(
            f"Fireworks API POST {url} failed with {response.status_code}: {snippet}"
        )
    return response.json() if response.content else {}


def upload_dataset_file(
    session: requests.Session,
    account_id: str,
    dataset_id: str,
    file_path: Path,
    *,
    max_retries: int = 5,
) -> dict[str, Any]:
    url = f"{API_ROOT}/v1/accounts/{account_id}/datasets/{dataset_id}:upload"
    response = None
    for attempt in range(max_retries):
        with file_path.open("rb") as handle:
            files = {"file": (file_path.name, handle)}
            response = _request_with_retries(
                session,
                "POST",
                url,
                max_retries=1,
                timeout=300,
                files=files,
            )
        if response.ok or response.status_code not in RETRYABLE_STATUS_CODES:
            break
        if attempt == max_retries - 1:
            break
        delay = _retry_sleep_seconds(response=response, attempt=attempt)
        print(
            f"Retrying dataset upload {urlparse(url).path} after HTTP "
            f"{response.status_code} ({attempt + 1}/{max_retries}, sleep={delay:.1f}s)"
        )
        time.sleep(delay)
    if not response.ok:
        snippet = response.text[:1000]
        raise RuntimeError(
            f"Fireworks dataset upload failed with "
            f"{response.status_code}: {snippet}"
        )
    if not response.content:
        return {}
    return response.json()


def create_batch_job(
    session: requests.Session,
    account_id: str,
    *,
    job_id: str,
    model: str,
    input_dataset_id: str,
    output_dataset_id: str,
    inference_parameters: dict[str, Any],
    display_name: str,
    max_retries: int = 5,
) -> dict[str, Any]:
    url = f"{API_ROOT}/v1/accounts/{account_id}/batchInferenceJobs"
    payload = {
        "displayName": display_name,
        "model": model,
        "inputDatasetId": dataset_name(account_id, input_dataset_id),
        "outputDatasetId": dataset_name(account_id, output_dataset_id),
        "inferenceParameters": inference_parameters,
    }
    response = _request_with_retries(
        session,
        "POST",
        url,
        max_retries=max_retries,
        timeout=120,
        params={"batchInferenceJobId": job_id},
        json=payload,
    )
    if response.status_code == 409:
        return get_batch_job(session, account_id, job_id, max_retries=max_retries)
    if not response.ok:
        snippet = response.text[:1000]
        raise RuntimeError(
            f"Fireworks API POST {url} failed with {response.status_code}: {snippet}"
        )
    return response.json() if response.content else {}


def get_batch_job(
    session: requests.Session,
    account_id: str,
    job_id: str,
    *,
    max_retries: int = 5,
) -> dict[str, Any]:
    url = f"{API_ROOT}/v1/accounts/{account_id}/batchInferenceJobs/{job_id}"
    return request_json(session, "GET", url, max_retries=max_retries)


def wait_for_batch_job(
    session: requests.Session,
    account_id: str,
    job_id: str,
    *,
    poll_interval: float,
    max_retries: int = 5,
) -> dict[str, Any]:
    while True:
        job = get_batch_job(session, account_id, job_id, max_retries=max_retries)
        state = (job.get("state") or "").replace("JOB_STATE_", "")
        progress = job.get("jobProgress") or {}
        percent = progress.get("percent")
        status = job.get("status") or {}
        message = status.get("message", "")
        if percent is None:
            print(f"[{job_id}] state={state or 'UNKNOWN'}")
        else:
            print(f"[{job_id}] state={state or 'UNKNOWN'} percent={percent}")
        if message:
            print(f"[{job_id}] status={message}")
        if state in TERMINAL_JOB_STATES:
            return job
        time.sleep(poll_interval)


def get_dataset_download_urls(
    session: requests.Session,
    account_id: str,
    dataset_id: str,
    *,
    max_retries: int = 5,
) -> dict[str, str]:
    url = (
        f"{API_ROOT}/v1/accounts/{account_id}/datasets/"
        f"{dataset_id}:getDownloadEndpoint"
    )
    payload = request_json(session, "GET", url, max_retries=max_retries)
    urls = payload.get("filenameToSignedUrls") or {}
    if not urls:
        raise RuntimeError("Fireworks returned no downloadable output files.")
    return urls


def download_signed_files(
    filename_to_url: dict[str, str],
    destination_dir: Path,
    *,
    max_retries: int = 5,
) -> list[Path]:
    requests = _requests_module()
    destination_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    for remote_name, signed_url in filename_to_url.items():
        local_name = Path(remote_name).name
        local_path = destination_dir / local_name
        last_error = None
        response = None
        for attempt in range(max_retries):
            try:
                response = requests.get(signed_url, timeout=300)
            except (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
            ) as exc:
                last_error = exc
                if attempt == max_retries - 1:
                    break
                delay = _retry_sleep_seconds(attempt=attempt)
                print(
                    f"Retrying file download {local_name} after transport failure "
                    f"({attempt + 1}/{max_retries}, sleep={delay:.1f}s): {exc}"
                )
                time.sleep(delay)
                continue
            if response.status_code in RETRYABLE_STATUS_CODES and attempt < max_retries - 1:
                delay = _retry_sleep_seconds(response=response, attempt=attempt)
                print(
                    f"Retrying file download {local_name} after HTTP "
                    f"{response.status_code} ({attempt + 1}/{max_retries}, sleep={delay:.1f}s)"
                )
                time.sleep(delay)
                continue
            break
        if response is None:
            raise RuntimeError(
                f"Failed to download {local_name} after {max_retries} attempts: {last_error}"
            ) from last_error
        response.raise_for_status()
        local_path.write_bytes(response.content)
        downloaded.append(local_path)
    return downloaded


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _coerce_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts).strip()
    if isinstance(value, dict):
        if "text" in value:
            return str(value["text"])
        if "content" in value:
            return _coerce_content(value["content"])
    return ""


def extract_batch_content(row: dict[str, Any]) -> str:
    candidates = [
        row.get("response", {}).get("body", {}).get("choices"),
        row.get("body", {}).get("choices"),
        row.get("result", {}).get("response", {}).get("body", {}).get("choices"),
        row.get("result", {}).get("body", {}).get("choices"),
    ]
    for choices in candidates:
        if not choices:
            continue
        message = choices[0].get("message", {})
        content = _coerce_content(message.get("content"))
        if content:
            return content.strip()

    for key in ("output_text", "content", "text"):
        content = _coerce_content(row.get(key))
        if content:
            return content.strip()

    raise RuntimeError(
        "Could not find assistant content in batch result row: "
        f"{json.dumps(row)[:500]}"
    )
