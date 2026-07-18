"""Provider transport for the DeepEval judge: HTTPS clients for OpenAI/Anthropic, image encoding, candidate PNG rendering/resolution, and the token-usage-tracking judge cache (StructuredJudgeBackend)."""
from __future__ import annotations

import base64
import json
import mimetypes
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lib.together_api import require_env, task_output_dir
from scripts.judge.judge_schema import (
    JudgeResult,
    SYSTEM_PROMPT,
    load_shared_judge_contract,
)


ROOT = Path(__file__).resolve().parents[2]

# Per-model pricing defaults (USD per 1M tokens).
# These are only used when --input-price-per-million / --output-price-per-million
# are not passed on the CLI; they remain fully overridable.
MODEL_PRICING_DEFAULTS: dict[tuple[str, str], tuple[float, float]] = {
    ("openai", "gpt-5.4"): (2.50, 15.00),
    # Claude Sonnet 5 introductory pricing ($2.00/$10.00) through 2026-08-31;
    # regular pricing is $3.00/$15.00.
    ("anthropic", "claude-sonnet-5"): (2.00, 10.00),
}


def estimate_cost_usd(
    *,
    input_tokens: int,
    output_tokens: int,
    input_price_per_million: float | None,
    output_price_per_million: float | None,
) -> float | None:
    """Convert token counts to a dollar cost, given caller-supplied per-million-token prices.

    Returns None (rather than guessing) when no price was supplied — model pricing
    changes over time, so this never hardcodes a rate.
    """
    if input_price_per_million is None or output_price_per_million is None:
        return None
    return (
        input_tokens / 1_000_000 * input_price_per_million
        + output_tokens / 1_000_000 * output_price_per_million
    )


def gval_task_dir(outputs_dir: Path, task_dir: Path) -> Path:
    """Return outputs/<model>/<category>/<difficulty>/<task_id>/gval for a task."""
    return task_output_dir(outputs_dir, task_dir) / "gval"


@dataclass
class TaskArtifacts:
    """Everything needed to judge one task: its directory, generated text, candidate PNG, and full judge prompt."""

    task_dir: Path
    output_text: str
    candidate_png: Path
    prompt: str


@dataclass
class TokenUsage:
    """Input/output/total token counts from a single judge API call."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class JudgeCallResult:
    """The raw return value of a provider client's .create() call: parsed result plus token usage."""

    result: JudgeResult
    usage: TokenUsage


@dataclass
class CachedJudgment:
    """A judge call's result, cached per (task_id, round_index) so repeated .measure() calls don't re-call the API."""

    result: JudgeResult
    candidate_png: Path
    usage: TokenUsage


def _requests_module() -> Any:
    """Import and return the `requests` package, or raise a friendly error if it's missing."""
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing `requests`. Install project dependencies with `uv sync`."
        ) from exc
    return requests


def encode_openai_image_data_url(image_path: Path) -> str:
    """Base64-encode an image into a data: URL for OpenAI's `input_image` content blocks."""
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def encode_anthropic_image_block(image_path: Path) -> dict[str, Any]:
    """Base64-encode an image into an Anthropic Messages API image content block."""
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


def resolve_candidate_png(task_dir: Path, outputs_dir: Path) -> Path:
    """Return the pre-rendered model-output PNG for a task."""
    png = task_output_dir(outputs_dir, task_dir) / f"{task_dir.name}.png"
    if not png.exists():
        raise FileNotFoundError(f"Missing model output PNG: {png}")
    return png


def build_prompt(task_dir: Path, output_text: str) -> str:
    """Fill the task's vlm_judge_prompt.txt template with the candidate output and append the shared judge contract.

    The candidate's rendered PNG is already attached as a real image in the
    judge call (for editing tasks, alongside the source and reference PNGs),
    so the MODEL OUTPUT text is always replaced with a placeholder rather
    than duplicating the raw ascii inline — the judge reads every diagram
    from the attached images, never from raw text.
    """
    del output_text  # unused: the judge reads the candidate diagram from the attached image
    prompt = (task_dir / "vlm_judge_prompt.txt").read_text().replace(
        "{model_output}",
        "[not included as text — see the attached candidate diagram image]",
    )
    return f"{prompt}\n\n{load_shared_judge_contract()}"


def _sleep_for_retry(attempt: int) -> None:
    """Exponential backoff sleep, capped at 30s, for judge API retries."""
    time.sleep(min(30.0, 1.5 * (2 ** attempt)))


def _extract_text_content(value: Any) -> str:
    """Pull plain text out of an Anthropic-style content block/list, or return a plain string as-is."""
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
    """Patch up minor judge-model JSON deviations (missing default list fields, misplaced semantics_score) before schema validation."""
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
    """Parse and validate a judge model's raw JSON text response into a JudgeResult."""
    payload = json.loads(json_text)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Judge response was not a JSON object: {type(payload)!r}")
    normalized = _normalize_judge_payload(payload)
    return response_model.model_validate(normalized)


def _token_usage_from_openai(data: dict[str, Any]) -> TokenUsage:
    """Extract token usage from an OpenAI Responses API JSON response."""
    usage = data.get("usage") or {}
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or (input_tokens + output_tokens))
    return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=total_tokens)


def _token_usage_from_anthropic(data: dict[str, Any]) -> TokenUsage:
    """Extract token usage from an Anthropic Messages API JSON response."""
    usage = data.get("usage") or {}
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=input_tokens + output_tokens)


class OpenAIHTTPSJudgeClient:
    """Direct HTTPS client for OpenAI's Responses API, used as the judge transport (no openai SDK dependency)."""

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
        temperature: float | None = None,
    ) -> JudgeCallResult:
        """POST to OpenAI's /v1/responses, retrying on failure, and return the parsed JudgeResult plus token usage."""
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
        if temperature is not None:
            payload["temperature"] = temperature
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
                result = _parse_judge_result(response_model, json_text)
                return JudgeCallResult(result=result, usage=_token_usage_from_openai(data))
            except Exception as exc:
                last_error = exc
                if attempt >= max_retries:
                    break
                _sleep_for_retry(attempt)
        raise RuntimeError(f"OpenAI judge request failed after retries: {last_error}") from last_error


class AnthropicHTTPSJudgeClient:
    """Direct HTTPS client for Anthropic's Messages API, used as the judge transport (no anthropic SDK dependency)."""

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
        temperature: float | None = None,
    ) -> JudgeCallResult:
        """POST to Anthropic's /v1/messages, retrying on failure, and return the parsed JudgeResult plus token usage."""
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
        if temperature is not None:
            payload["temperature"] = temperature
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
                result = _parse_judge_result(response_model, json_text)
                return JudgeCallResult(result=result, usage=_token_usage_from_anthropic(data))
            except Exception as exc:
                last_error = exc
                if attempt >= max_retries:
                    break
                _sleep_for_retry(attempt)
        raise RuntimeError(f"Anthropic judge request failed after retries: {last_error}") from last_error


class ProviderChatCompletionsAdapter:
    """Exposes a provider client's .create() under a `.chat.completions.create(...)` path, mimicking the OpenAI SDK shape StructuredJudgeBackend expects."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def create(self, **kwargs: Any) -> JudgeCallResult:
        return self._client.create(**kwargs)


class ProviderChatAdapter:
    """The `.chat` half of ProviderClientAdapter's OpenAI-SDK-shaped interface."""

    def __init__(self, client: Any) -> None:
        self.completions = ProviderChatCompletionsAdapter(client)


class ProviderClientAdapter:
    """Wraps an OpenAIHTTPSJudgeClient/AnthropicHTTPSJudgeClient so callers can use `.chat.completions.create(...)` regardless of provider."""

    def __init__(self, client: Any) -> None:
        self.chat = ProviderChatAdapter(client)


def create_openai_client() -> Any:
    """Build an OpenAI-SDK-shaped judge client backed by OpenAIHTTPSJudgeClient."""
    return ProviderClientAdapter(OpenAIHTTPSJudgeClient(require_env("OPENAI_API_KEY")))


def create_anthropic_client() -> Any:
    """Build an OpenAI-SDK-shaped judge client backed by AnthropicHTTPSJudgeClient."""
    return ProviderClientAdapter(AnthropicHTTPSJudgeClient(require_env("ANTHROPIC_API_KEY")))


def create_provider_client(provider: str) -> Any:
    """Build the judge client for "openai" or "anthropic"."""
    if provider == "openai":
        return create_openai_client()
    if provider == "anthropic":
        return create_anthropic_client()
    raise ValueError(f"Unsupported provider: {provider}")


EVAL_MARKER = "Evaluate this task with the same rubric used for every benchmark task."


def _split_prompt_around_images(prompt: str) -> tuple[str, str]:
    """Split the filled prompt into a pre-image half (task/prompt/assertions/model output) and a post-image half (the scoring rubric, which starts at EVAL_MARKER), so images can be placed between them per multimodal best practice (images before the text that reasons about them)."""
    if EVAL_MARKER not in prompt:
        raise RuntimeError(f"Expected marker not found in judge prompt: {EVAL_MARKER!r}")
    before, _, after = prompt.partition(EVAL_MARKER)
    return before.rstrip(), EVAL_MARKER + after


def build_user_content(
    provider: str,
    task_dir: Path,
    prompt: str,
    candidate_png: Path,
) -> Any:
    """Build the provider-specific multimodal user message: task text, then explicitly labeled images, then the scoring rubric text.

    Images are placed before the rubric/instructions that reason about them
    (Anthropic and general multimodal guidance: put images ahead of the text
    referencing them, not after). Image order for editing tasks is source,
    candidate, reference — the candidate sits in the middle so it is
    positionally adjacent to both images it must be compared against (source
    for what should be preserved, reference for whether the edit is
    correct), rather than adjacent to only one of them.
    """
    is_editing = (task_dir / "source.ascii").exists()
    before, after = _split_prompt_around_images(prompt)

    if is_editing:
        image_order_note = (
            "You will receive three images in this exact order: Image 1 is the original "
            "diagram (the baseline before the edit), Image 2 is the candidate diagram (the "
            "model's output to judge), and Image 3 is the reference diagram (what the correct "
            "result should look like). Treating Image 1 as the original, compare Image 3 "
            "against Image 2 to check whether the requested edit produced the correct result, "
            "and use Image 1 to check that everything outside the edit was preserved."
        )
    else:
        image_order_note = (
            "You will receive two images in this exact order: Image 1 is the reference diagram "
            "(what the correct result should look like), and Image 2 is the candidate diagram "
            "(the model's output to judge)."
        )

    if provider == "openai":
        blocks: list[dict[str, Any]] = [
            {"type": "input_text", "text": before},
            {"type": "input_text", "text": image_order_note},
        ]
        if is_editing:
            blocks.append({"type": "input_text", "text": "Source diagram (the baseline before the edit):"})
            blocks.append(
                {
                    "type": "input_image",
                    "image_url": encode_openai_image_data_url(task_dir / "source.png"),
                }
            )
        blocks.append({"type": "input_text", "text": "Candidate diagram (the model's output to judge):"})
        blocks.append(
            {
                "type": "input_image",
                "image_url": encode_openai_image_data_url(candidate_png),
            }
        )
        blocks.append({"type": "input_text", "text": "Reference diagram (what the correct result should look like):"})
        blocks.append(
            {
                "type": "input_image",
                "image_url": encode_openai_image_data_url(task_dir / "reference.png"),
            }
        )
        blocks.append({"type": "input_text", "text": after})
        return [{"role": "user", "content": blocks}]

    if provider == "anthropic":
        content: list[dict[str, Any]] = [
            {"type": "text", "text": before},
            {"type": "text", "text": image_order_note},
        ]
        if is_editing:
            content.append({"type": "text", "text": "Source diagram (the baseline before the edit):"})
            content.append(encode_anthropic_image_block(task_dir / "source.png"))
        content.append({"type": "text", "text": "Candidate diagram (the model's output to judge):"})
        content.append(encode_anthropic_image_block(candidate_png))
        content.append({"type": "text", "text": "Reference diagram (what the correct result should look like):"})
        content.append(encode_anthropic_image_block(task_dir / "reference.png"))
        content.append({"type": "text", "text": after})
        return content

    raise ValueError(f"Unsupported provider: {provider}")


def build_readable_prompt_text(task_dir: Path, prompt: str) -> str:
    """Build a human-readable stand-in for the multimodal user message: the same task text / image-order note / rubric split used by build_user_content, with image placeholders (not raw base64) in the same order actually sent to the judge, for saving to gval/final_prompt.txt."""
    is_editing = (task_dir / "source.ascii").exists()
    before, after = _split_prompt_around_images(prompt)

    if is_editing:
        image_order_note = (
            "You will receive three images in this exact order: Image 1 is the original "
            "diagram (the baseline before the edit), Image 2 is the candidate diagram (the "
            "model's output to judge), and Image 3 is the reference diagram (what the correct "
            "result should look like). Treating Image 1 as the original, compare Image 3 "
            "against Image 2 to check whether the requested edit produced the correct result, "
            "and use Image 1 to check that everything outside the edit was preserved."
        )
    else:
        image_order_note = (
            "You will receive two images in this exact order: Image 1 is the reference diagram "
            "(what the correct result should look like), and Image 2 is the candidate diagram "
            "(the model's output to judge)."
        )

    sections = [before, image_order_note]
    if is_editing:
        sections.append("Source diagram (the baseline before the edit): [image attached — see source.png in this folder]")
    sections.append("Candidate diagram (the model's output to judge): [image attached — see candidate.png in this folder]")
    sections.append("Reference diagram (what the correct result should look like): [image attached — see reference.png in this folder]")
    sections.append(after)
    return "\n\n".join(sections)


class StructuredJudgeBackend:
    """Runs (and caches, per task_id + round_index) judge calls against one provider/model for a batch of tasks."""

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        max_retries: int,
        artifacts_by_task_id: dict[str, TaskArtifacts],
        outputs_dir: Path,
        temperature: float | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.max_retries = max_retries
        self.artifacts_by_task_id = artifacts_by_task_id
        self.outputs_dir = outputs_dir
        self.temperature = temperature
        self.client = create_provider_client(provider)
        self.cache: dict[tuple[str, int], CachedJudgment] = {}

    def judge(self, task_id: str, round_index: int = 0) -> CachedJudgment:
        """Judge a task (or return the cached result if this exact (task_id, round_index) was already judged)."""
        cache_key = (task_id, round_index)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        artifacts = self.artifacts_by_task_id[task_id]
        user_content = build_user_content(
            self.provider,
            artifacts.task_dir,
            artifacts.prompt,
            artifacts.candidate_png,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        call_result = self.client.chat.completions.create(
            model=self.model,
            response_model=JudgeResult,
            max_retries=self.max_retries,
            temperature=self.temperature,
            messages=messages,
        )
        cached = CachedJudgment(
            result=call_result.result,
            candidate_png=artifacts.candidate_png,
            usage=call_result.usage,
        )
        self.cache[cache_key] = cached

        # Save the judge prompt and the actual images it saw, for human
        # inspection. The prompt text uses placeholders instead of raw
        # base64 (the API call above already sent the real image data).
        import shutil

        gval_dir = gval_task_dir(self.outputs_dir, artifacts.task_dir)
        gval_dir.mkdir(parents=True, exist_ok=True)
        source_png = artifacts.task_dir / "source.png"
        if source_png.exists():
            shutil.copy2(source_png, gval_dir / "source.png")
        shutil.copy2(artifacts.task_dir / "reference.png", gval_dir / "reference.png")
        shutil.copy2(artifacts.candidate_png, gval_dir / "candidate.png")

        readable_user_content = build_readable_prompt_text(artifacts.task_dir, artifacts.prompt)
        (gval_dir / "final_prompt.txt").write_text(
            f"SYSTEM:\n{SYSTEM_PROMPT}\n\nUSER:\n{readable_user_content}"
        )
        return cached


def build_task_artifacts(task_dir: Path, outputs: Path) -> TaskArtifacts:
    """Assemble a task's generated text, candidate PNG, and full judge prompt into a TaskArtifacts."""
    output_text = (task_output_dir(outputs, task_dir) / f"{task_dir.name}.txt").read_text().strip()
    candidate_png = resolve_candidate_png(task_dir, outputs)
    return TaskArtifacts(
        task_dir=task_dir,
        output_text=output_text,
        candidate_png=candidate_png,
        prompt=build_prompt(task_dir, output_text),
    )
