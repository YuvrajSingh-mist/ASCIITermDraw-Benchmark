#!/usr/bin/env python3
"""OpenRouter synchronous chat-completions transport, .env loading, and tasks/ directory helpers shared across the generation and judging scripts."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


API_ROOT = "https://openrouter.ai/api"
TASK_ID_RE = re.compile(r"^\d+\.\d+$")
RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
ROOT = Path(__file__).resolve().parents[2]


def _candidate_env_files() -> list[Path]:
    """List every `.env.local`/`.env` path worth checking, nearest-first, deduplicated."""
    files: list[Path] = []
    seen: set[Path] = set()

    search_roots = [Path.cwd(), *Path.cwd().parents, ROOT, *ROOT.parents[:2]]
    for base in search_roots:
        for name in (".env.local", ".env"):
            path = (base / name).resolve()
            if path in seen:
                continue
            seen.add(path)
            files.append(path)
    return files


def load_local_env() -> None:
    """Populate os.environ from the first matching .env.local/.env file, without overwriting values already set."""
    for env_file in _candidate_env_files():
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


def require_env(name: str) -> str:
    """Return the named environment variable, or raise if it's missing/blank."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _retry_sleep_seconds(response=None, attempt: int = 0) -> float:
    """Pick a retry delay: honor a Retry-After header if present, else exponential backoff capped at 30s."""
    if response is not None:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
    return min(30.0, 1.5 * (2 ** attempt))


class CurlHTTPError(RuntimeError):
    """An HTTP error response (status >= 400) from a curl-based request, with the status code and body attached."""

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
    """POST a JSON payload via the `curl` binary and return the parsed JSON response, raising CurlHTTPError on non-2xx."""
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
            "-H",
            "HTTP-Referer: https://github.com/YuvrajSingh-mist/ASCIITermDraw-Benchmark",
            "-H",
            "X-Title: ASCIITermDraw-Bench",
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


# Upstream providers observed to ignore OpenRouter's unified
# `{"reasoning": {"enabled": false}}` for at least one model: they reason
# anyway, burning the whole max_tokens budget before producing any real
# output (empty content, finish_reason "length"). Excluded via OpenRouter's
# provider-routing `ignore` field whenever reasoning is meant to be off,
# rather than papering over the symptom by inflating max_tokens.
#   - novita: 5/5 failures pinned for minimax/minimax-m3, 5/5 successes once
#     excluded (every other upstream -- Minimax official, DeepInfra,
#     Together, GMICloud, Venice, AtlasCloud -- honored the flag correctly).
#   - digitalocean: hit live during a real 80-task moonshotai/kimi-k2.6 run
#     (task 27/80 failed with this exact signature, routed through
#     DigitalOcean).
NON_COMPLIANT_REASONING_PROVIDERS = ["novita", "digitalocean"]


def chat_completion_with_retries(
    api_key: str,
    *,
    model: str,
    messages: list[dict[str, Any]],
    reasoning_effort: str,
    network_retries: int,
    max_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    seed: int | None = None,
    timeout: int | float = 90,
    request_label: str = "chat completion",
) -> dict[str, Any]:
    """Call OpenRouter's synchronous chat-completions endpoint, retrying on retryable HTTP codes/timeouts/transport errors.

    `max_tokens`/`temperature`/`top_p`/`seed` are omitted from the request payload
    when left as None, so the model falls back to its own defaults instead of a
    hardcoded value. `seed` is best-effort determinism (provider-dependent, not
    a hard guarantee) — it narrows but doesn't guarantee bit-identical outputs
    across calls, especially at larger max_tokens. `reasoning_effort` of "none"
    sends OpenRouter's unified `{"reasoning": {"enabled": false}}` -- some
    models (e.g. Qwen3.7-Plus) reason by default even with no `reasoning` field
    at all, silently inflating completion tokens/cost, so this has to be sent
    explicitly rather than just omitted. Any other value ("low"/"medium"/"high")
    is passed through as `{"reasoning": {"effort": reasoning_effort}}`. When
    reasoning is disabled, `provider.ignore` also excludes upstream providers
    known to not honor that flag for at least one model (see
    NON_COMPLIANT_REASONING_PROVIDERS) -- routing away from them, not
    inflating max_tokens, is the actual fix for the empty-content-on-length
    failure this previously caused.
    """
    payload = {
        "model": model,
        "messages": messages,
    }
    if reasoning_effort and reasoning_effort != "none":
        payload["reasoning"] = {"effort": reasoning_effort}
    else:
        payload["reasoning"] = {"enabled": False}
        payload["provider"] = {"ignore": NON_COMPLIANT_REASONING_PROVIDERS}
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if top_p is not None:
        payload["top_p"] = top_p
    if seed is not None:
        payload["seed"] = seed
    last_error = None
    for attempt in range(network_retries):
        try:
            return _curl_json_request(
                api_key,
                url=f"{API_ROOT}/v1/chat/completions",
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
                f"OpenRouter {request_label} failed with HTTP {exc.status_code}: "
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


def task_sort_key(task_id: str) -> tuple[int, float]:
    """Sort key for a task id like "2.11": (category as int, "category.minor" as float)."""
    category, remainder = task_id.split(".", 1)
    return int(category), float(f"{category}.{remainder}")


def iter_task_dirs(tasks_dir: Path) -> list[Path]:
    """List every task directory under tasks_dir (any dir named like a task id, e.g. "2.11"), sorted by task_sort_key."""
    return sorted(
        [
            path
            for path in tasks_dir.rglob("*")
            if path.is_dir() and TASK_ID_RE.fullmatch(path.name)
        ],
        key=lambda path: task_sort_key(path.name),
    )


def task_output_dir(outputs_dir: Path, task_dir: Path) -> Path:
    """Mirror a task's `category/difficulty/task_id` layout under an outputs dir.

    `task_dir` is expected to be `<tasks_root>/<category>/<difficulty>/<task_id>`
    (as returned by `iter_task_dirs`), so the last three path components are
    reused directly without needing the tasks root.
    """
    return outputs_dir / task_dir.parent.parent.name / task_dir.parent.name / task_dir.name


def _coerce_content(value: Any) -> str:
    """Best-effort extraction of plain text from a chat-completion message `content` field, whatever shape it's in."""
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


def extract_chat_content(row: dict[str, Any]) -> str:
    """Pull the assistant's text reply out of an OpenRouter chat-completion response, trying a few known response shapes."""
    candidates = [
        row.get("choices"),
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
        "Could not find assistant content in response row: "
        f"{json.dumps(row)[:500]}"
    )


def extract_usage(row: dict[str, Any]) -> dict[str, Any] | None:
    """Pull token usage (and OpenRouter's own reported dollar cost, if present) out of a chat-completion response, trying the same nesting shapes as extract_chat_content. Returns None if no usage block is present.

    OpenRouter reports the real per-request cost directly as `usage.cost` (a
    provider-side computed number, not an estimate) -- this is preferred over
    MODEL_PRICING_DEFAULTS-based estimation whenever it's present.
    """
    candidates = [
        row.get("usage"),
        row.get("response", {}).get("body", {}).get("usage"),
        row.get("body", {}).get("usage"),
        row.get("result", {}).get("response", {}).get("body", {}).get("usage"),
        row.get("result", {}).get("body", {}).get("usage"),
    ]
    for usage in candidates:
        if not usage:
            continue
        result: dict[str, Any] = {
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }
        if usage.get("cost") is not None:
            result["real_cost_usd"] = float(usage["cost"])
        return result
    return None


def estimate_cost_usd(
    *,
    input_tokens: int,
    output_tokens: int,
    input_price_per_million: float | None,
    output_price_per_million: float | None,
) -> float | None:
    """Convert token counts to a dollar cost, given caller-supplied per-million-token prices.

    Returns None (rather than guessing) when no price was supplied — model pricing
    changes over time, so this never hardcodes a rate the caller didn't provide.
    """
    if input_price_per_million is None or output_price_per_million is None:
        return None
    return (
        input_tokens / 1_000_000 * input_price_per_million
        + output_tokens / 1_000_000 * output_price_per_million
    )
