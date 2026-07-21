#!/usr/bin/env python3
"""Ollama native chat backend used by the generation runners."""
from __future__ import annotations

import base64
import time
from typing import Any

import requests


RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


def _ollama_message(message: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAI-style text/image message to Ollama's native shape."""
    content = message.get("content", "")
    if isinstance(content, str):
        return {"role": message["role"], "content": content}

    text_parts: list[str] = []
    images: list[str] = []
    for block in content:
        if block.get("type") == "text":
            text_parts.append(str(block.get("text", "")))
        elif block.get("type") == "image_url":
            image_url = block.get("image_url", {}).get("url", "")
            if not image_url.startswith("data:") or ";base64," not in image_url:
                raise RuntimeError("Ollama image inputs must be inline base64 data URLs.")
            encoded = image_url.split(";base64,", 1)[1]
            # Validate early so a malformed task fails with a useful local error.
            base64.b64decode(encoded, validate=True)
            images.append(encoded)

    result: dict[str, Any] = {
        "role": message["role"],
        "content": "\n\n".join(text_parts),
    }
    if images:
        result["images"] = images
    return result


def chat_completion_with_retries(
    *,
    host: str,
    model: str,
    messages: list[dict[str, Any]],
    reasoning_effort: str,
    network_retries: int,
    max_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    seed: int | None = None,
    timeout: int | float = 1800,
    request_label: str = "chat completion",
) -> dict[str, Any]:
    """Call Ollama's native non-streaming chat endpoint with transient retries."""
    options: dict[str, Any] = {}
    if temperature is not None:
        options["temperature"] = temperature
    if max_tokens is not None:
        options["num_predict"] = max_tokens
    if top_p is not None:
        options["top_p"] = top_p
    if seed is not None:
        options["seed"] = seed

    payload: dict[str, Any] = {
        "model": model,
        "messages": [_ollama_message(message) for message in messages],
        "stream": False,
        "options": options,
        "keep_alive": "30m",
    }
    # Current Ollama accepts a boolean or effort string. Older releases may
    # reject `think`; retry once without it for compatibility.
    payload["think"] = False if not reasoning_effort or reasoning_effort == "none" else reasoning_effort

    url = f"{host.rstrip('/')}/api/chat"
    last_error: Exception | None = None
    for attempt in range(network_retries):
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            if response.status_code == 400 and "think" in payload and "think" in response.text.lower():
                payload.pop("think")
                response = requests.post(url, json=payload, timeout=timeout)
            if response.status_code >= 400:
                message = f"HTTP {response.status_code}: {response.text[:1500]}"
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    raise RuntimeError(f"Ollama {request_label} failed with {message}")
                raise requests.HTTPError(message, response=response)
            row = response.json()
            return {
                "choices": [{"message": {"content": row.get("message", {}).get("content", "")}}],
                "usage": {
                    "prompt_tokens": int(row.get("prompt_eval_count", 0)),
                    "completion_tokens": int(row.get("eval_count", 0)),
                    "total_tokens": int(row.get("prompt_eval_count", 0)) + int(row.get("eval_count", 0)),
                },
                "ollama": {
                    "total_duration": row.get("total_duration"),
                    "load_duration": row.get("load_duration"),
                    "prompt_eval_duration": row.get("prompt_eval_duration"),
                    "eval_duration": row.get("eval_duration"),
                },
            }
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            if attempt == network_retries - 1:
                break
            delay = min(30.0, 1.5 * (2**attempt))
            print(
                f"Retrying Ollama {request_label} after transport failure "
                f"({attempt + 1}/{network_retries}, sleep={delay:.1f}s): {exc}"
            )
            time.sleep(delay)
    raise RuntimeError(f"No Ollama response received for {request_label}: {last_error}")
