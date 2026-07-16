from __future__ import annotations

import base64
import json
import mimetypes
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lib.fireworks_api import require_env
from scripts.judge.run_vlm_judge import (
    JudgeResult,
    SYSTEM_PROMPT,
    load_shared_judge_contract,
)


ROOT = Path(__file__).resolve().parents[2]


@dataclass
class TaskArtifacts:
    task_dir: Path
    output_text: str
    candidate_png: Path
    prompt: str


@dataclass
class CachedJudgment:
    result: JudgeResult
    candidate_png: Path


def _requests_module() -> Any:
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing `requests`. Install project dependencies with `uv sync`."
        ) from exc
    return requests


def encode_openai_image_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def encode_anthropic_image_block(image_path: Path) -> dict[str, Any]:
    media_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": encoded,
        },
    }


def render_ascii_to_png(ascii_text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".ascii", delete=False) as tmp:
        tmp.write(ascii_text.rstrip("\n") + "\n")
        temp_ascii_path = Path(tmp.name)
    try:
        subprocess.run(
            [
                "node",
                str(ROOT / "scripts" / "rendered" / "render_ascii.mjs"),
                str(temp_ascii_path),
                str(output_path),
            ],
            check=True,
            timeout=60,
        )
    finally:
        temp_ascii_path.unlink(missing_ok=True)


def resolve_candidate_png(task_dir: Path, outputs_dir: Path) -> Path:
    rendered_dir = outputs_dir / "judge_geval_rendered"
    candidate_png = rendered_dir / f"{task_dir.name}.png"
    if candidate_png.exists():
        return candidate_png

    pre_rendered_png = outputs_dir / f"{task_dir.name}.png"
    if pre_rendered_png.exists():
        return pre_rendered_png

    output_file = outputs_dir / f"{task_dir.name}.txt"
    output_text = output_file.read_text().strip()
    render_ascii_to_png(output_text, candidate_png)
    return candidate_png


def build_prompt(task_dir: Path, output_text: str) -> str:
    prompt = (task_dir / "vlm_judge_prompt.txt").read_text().replace(
        "{model_output}",
        output_text,
    )
    return f"{prompt}\n\n{load_shared_judge_contract()}"


def _sleep_for_retry(attempt: int) -> None:
    time.sleep(min(30.0, 1.5 * (2 ** attempt)))


def _extract_text_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        chunks: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        return "\n".join(chunks).strip()
    raise RuntimeError(f"Unsupported response content format: {type(value)!r}")


def _normalize_judge_payload(payload: dict[str, Any]) -> dict[str, Any]:
    structural = payload.get("structural_observations")
    if isinstance(structural, dict):
        structural.setdefault("required_edge_labels_present", [])
        structural.setdefault("preserved_elements_present", [])

    semantics = payload.get("semantics")
    if isinstance(semantics, dict) and "semantics_score" not in semantics:
        if "semantics_score" in payload:
            semantics["semantics_score"] = payload.pop("semantics_score")

    return payload


def _parse_judge_result(response_model: type[JudgeResult], json_text: str) -> JudgeResult:
    payload = json.loads(json_text)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Judge response was not a JSON object: {type(payload)!r}")
    normalized = _normalize_judge_payload(payload)
    return response_model.model_validate(normalized)


class OpenAIHTTPSJudgeClient:
    def __init__(self, api_key: str) -> None:
        requests = _requests_module()
        self.requests = requests
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    def create(
        self,
        *,
        model: str,
        response_model: type[JudgeResult],
        max_retries: int,
        messages: list[dict[str, Any]],
    ) -> JudgeResult:
        payload = {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": messages[0]["content"]}],
                },
                *messages[1]["content"],
            ],
            "text": {
                "format": {
                    "type": "json_object",
                }
            },
        }
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                response = self.session.post(
                    "https://api.openai.com/v1/responses",
                    data=json.dumps(payload),
                    timeout=180,
                )
                if not response.ok:
                    raise RuntimeError(
                        f"HTTP {response.status_code}: {response.text[:2000]}"
                    )
                data = response.json()
                json_text = data.get("output_text", "")
                if not json_text:
                    output = data.get("output", [])
                    if output and isinstance(output, list):
                        first = output[0]
                        if isinstance(first, dict):
                            content = first.get("content", [])
                            json_text = _extract_text_content(content)
                if not json_text:
                    raise RuntimeError(
                        f"Missing output text in OpenAI response: {json.dumps(data)[:2000]}"
                    )
                return _parse_judge_result(response_model, json_text)
            except Exception as exc:
                last_error = exc
                if attempt >= max_retries:
                    break
                _sleep_for_retry(attempt)
        raise RuntimeError(f"OpenAI judge request failed after retries: {last_error}") from last_error


class AnthropicHTTPSJudgeClient:
    def __init__(self, api_key: str) -> None:
        requests = _requests_module()
        self.requests = requests
        self.session = requests.Session()
        self.session.headers.update(
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
        )

    def create(
        self,
        *,
        model: str,
        response_model: type[JudgeResult],
        max_retries: int,
        messages: list[dict[str, Any]],
    ) -> JudgeResult:
        system_prompt = messages[0]["content"]
        user_message = messages[1]
        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {
                    "role": user_message["role"],
                    "content": user_message["content"],
                }
            ],
        }
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                response = self.session.post(
                    "https://api.anthropic.com/v1/messages",
                    data=json.dumps(payload),
                    timeout=180,
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("content", [])
                json_text = _extract_text_content(content)
                return _parse_judge_result(response_model, json_text)
            except Exception as exc:
                last_error = exc
                if attempt >= max_retries:
                    break
                _sleep_for_retry(attempt)
        raise RuntimeError(f"Anthropic judge request failed after retries: {last_error}") from last_error


class ProviderChatCompletionsAdapter:
    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, **kwargs: Any) -> JudgeResult:
        return self._client.create(**kwargs)


class ProviderChatAdapter:
    def __init__(self, client: Any) -> None:
        self.completions = ProviderChatCompletionsAdapter(client)


class ProviderClientAdapter:
    def __init__(self, client: Any) -> None:
        self.chat = ProviderChatAdapter(client)


def create_openai_client() -> Any:
    return ProviderClientAdapter(OpenAIHTTPSJudgeClient(require_env("OPENAI_API_KEY")))


def create_anthropic_client() -> Any:
    return ProviderClientAdapter(AnthropicHTTPSJudgeClient(require_env("ANTHROPIC_API_KEY")))


def create_provider_client(provider: str) -> Any:
    if provider == "openai":
        return create_openai_client()
    if provider == "anthropic":
        return create_anthropic_client()
    raise ValueError(f"Unsupported provider: {provider}")


def build_user_content(
    provider: str,
    task_dir: Path,
    prompt: str,
    candidate_png: Path,
) -> Any:
    if provider == "openai":
        blocks: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
        if (task_dir / "source.ascii").exists():
            blocks.append(
                {
                    "type": "input_image",
                    "image_url": encode_openai_image_data_url(task_dir / "source.png"),
                }
            )
        blocks.extend(
            [
                {
                    "type": "input_image",
                    "image_url": encode_openai_image_data_url(task_dir / "reference.png"),
                },
                {
                    "type": "input_image",
                    "image_url": encode_openai_image_data_url(candidate_png),
                },
            ]
        )
        return [{"role": "user", "content": blocks}]

    if provider == "anthropic":
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if (task_dir / "source.ascii").exists():
            content.append(encode_anthropic_image_block(task_dir / "source.png"))
        content.extend(
            [
                encode_anthropic_image_block(task_dir / "reference.png"),
                encode_anthropic_image_block(candidate_png),
            ]
        )
        return content

    raise ValueError(f"Unsupported provider: {provider}")


class StructuredJudgeBackend:
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        max_retries: int,
        artifacts_by_task_id: dict[str, TaskArtifacts],
    ) -> None:
        self.provider = provider
        self.model = model
        self.max_retries = max_retries
        self.artifacts_by_task_id = artifacts_by_task_id
        self.client = create_provider_client(provider)
        self.cache: dict[str, CachedJudgment] = {}

    def judge(self, task_id: str) -> CachedJudgment:
        cached = self.cache.get(task_id)
        if cached is not None:
            return cached

        artifacts = self.artifacts_by_task_id[task_id]
        result = self.client.chat.completions.create(
            model=self.model,
            response_model=JudgeResult,
            max_retries=self.max_retries,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_user_content(
                        self.provider,
                        artifacts.task_dir,
                        artifacts.prompt,
                        artifacts.candidate_png,
                    ),
                },
            ],
        )
        cached = CachedJudgment(result=result, candidate_png=artifacts.candidate_png)
        self.cache[task_id] = cached
        return cached


def build_task_artifacts(task_dir: Path, outputs: Path) -> TaskArtifacts:
    output_text = (outputs / f"{task_dir.name}.txt").read_text().strip()
    candidate_png = resolve_candidate_png(task_dir, outputs)
    return TaskArtifacts(
        task_dir=task_dir,
        output_text=output_text,
        candidate_png=candidate_png,
        prompt=build_prompt(task_dir, output_text),
    )
