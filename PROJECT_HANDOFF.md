# ASCIITermDraw Benchmark Handoff

## Purpose

This repository contains a benchmark for ASCII diagram generation and ASCII diagram editing.

The benchmark is designed to evaluate:

1. Basic box/layout correctness
2. Network topology diagram generation
3. Diagram editing fidelity
4. Real-world software architecture diagram generation

The intended workflow is:

1. Generate ASCII outputs from a model
2. Render those ASCII outputs to PNG
3. Judge the results with a multimodal model
4. Compute a structural score and a semantic score

## Core Benchmark Contract

Each task contains task-local metadata and assets under `tasks/.../<difficulty>/<task_id>/`.

Important files:

- `prompt.txt`
- `assertions.json`
- `vlm_judge_prompt.txt`
- `reference.ascii`
- `reference.png`
- for editing tasks also `source.ascii` and `source.png`

### Scoring

The final benchmark score is:

`score = structural_score + semantics_score`

#### Structural score

This is deterministic harness-side scoring.

The judge model returns factual evidence in JSON:

- `required_labels_present`
- `entity_count_observed`
- `required_edges_present`
- for editing tasks:
  - `required_edge_labels_present`
  - `preserved_elements_present`

The harness compares that evidence against `assertions.json`.

Structural components are currently binary component checks averaged together when present.

#### Semantic score

This is judge-model scoring.

The judge evaluates:

- `connections_correct`
- `text_inside_nodes_correct`
- `text_centered_in_nodes`
- `layout_matches_prompt`
- `labels_spelled_correct`
- `arrows_cleanly_aligned`
- `semantics_score` as a float from `0.0` to `1.0`

The benchmark treats `semantics_score` as the actual semantic score, while preserving the binary fields for transparency/debugging.

## Judge Architecture

There are two related judge paths in `scripts/judge/`.

### 1. Fireworks structured judge

File:

- `scripts/judge/run_vlm_judge.py`

This path uses the Fireworks-compatible OpenAI interface plus Pydantic models for structured parsing.

It is mainly useful for synchronous structured judging.

### 2. DeepEval BaseMetric judge runner

Files:

- `scripts/judge/run_geval_judge.py`
- `scripts/judge/geval_metrics.py`
- `scripts/judge/geval_support.py`
- `scripts/judge/shared_judge_contract.txt`

Important clarification:

- This uses the actual `deepeval` package via `BaseMetric`
- It does **not** use the built-in `GEval` class for the full benchmark contract

Why:

- built-in `GEval` is not a clean fit for structural evidence extraction plus `assertions.json` comparison
- `BaseMetric` is the official DeepEval extension point for custom metrics when built-in metrics are insufficient

So the benchmark currently uses:

- DeepEval `BaseMetric` for integration/lifecycle
- a custom multimodal judge call for scoring
- task-specific judge prompts
- deterministic harness-side structural scoring

## Shared Judge Contract

The shared judge instructions live in:

- `scripts/judge/shared_judge_contract.txt`

This is appended to each task’s `vlm_judge_prompt.txt`.

This file explains:

- what `structural_observations` means
- what `semantics` means
- that `semantics_score` must be returned directly
- that the response must match the expected JSON shape

## Provider Responsibilities

### Generation

Generation is intended to use Fireworks models.

Relevant scripts:

- `scripts/run_model.py`
- `scripts/smoke_generate.py`

### Judge

Judge providers are OpenAI and Anthropic.

OpenAI and Anthropic are used for multimodal judging.

Current design direction:

- use DeepEval `BaseMetric` for the metric wrapper
- use direct HTTPS transport for judge calls where possible
- keep Pydantic validation at the harness level

## Current File-Level State

### Important judge files

- `scripts/judge/run_geval_judge.py`
  - thin runner
  - iterates tasks
  - writes per-task JSON and CSV outputs

- `scripts/judge/geval_metrics.py`
  - defines the custom DeepEval `BaseMetric` classes
  - one structural metric
  - one semantic metric

- `scripts/judge/geval_support.py`
  - provider request building
  - prompt construction
  - multimodal input assembly
  - result caching
  - currently contains transport logic for OpenAI/Anthropic judge calls

- `scripts/judge/run_vlm_judge.py`
  - Pydantic result schema
  - structural scoring logic
  - semantic score extraction logic

## Environment Notes

### Python

The repo is intended to run with `uv`.

`pyproject.toml` currently targets:

- `requires-python = ">=3.10"`

### Local env loading

Environment values are loaded through `scripts/lib/fireworks_api.py`.

That file searches for `.env.local` and `.env`.

### Known machine observations

On the machine used during this session:

- Apple Silicon Mac (`arm64`)
- disk usage was high
- memory pressure/compression activity was non-trivial

However, the main blocker encountered was not “M1 incompatibility”.

The main startup slowdown came from heavyweight package import chains.

## What Was Learned About DeepEval

DeepEval `BaseMetric` is the official way to build custom metrics.

According to DeepEval docs, use `BaseMetric` when:

- you need more control than `GEval` or `DAG`
- you need custom scoring logic
- you want to combine or customize evaluation behavior

This benchmark fits that case because:

- structural evidence must be extracted by a judge
- structural score must then be computed programmatically
- semantic score must still come from the judge model

So the benchmark is best described as:

- DeepEval `BaseMetric` integration
- custom multimodal judge implementation
- GEval-inspired semantic rubric

Not:

- “everything is the built-in GEval metric”

## Render Pipeline

ASCII outputs are rendered to PNG for judging.

Relevant files:

- `scripts/rendered/render_ascii.mjs`
- `scripts/rendered/render.py`
- `scripts/rendered/render_all.py`

Generation scripts were updated earlier so PNG rendering happens when model outputs are written.

## Commands

Common commands:

```bash
uv sync
uv run smoke --model accounts/fireworks/models/qwen3-vl-8b-instruct --tasks tasks --oneshot oneshot --outputs outputs/smoke --sample-count 5 --seed 7 --reasoning-effort none --network-retries 5
uv run judge --model accounts/fireworks/models/qwen3-vl-8b-instruct --tasks tasks --outputs outputs/smoke --results outputs/judge_results.csv
uv run judge-geval --provider openai --model gpt-5.4 --tasks tasks --outputs outputs/smoke --results outputs/geval_results.csv
```

Note:

- exact provider/model names may change
- always verify current supported judge model names before large runs

## Current Known Issues

These are the most important unresolved items after this session:

1. The repo is back to importing the actual `deepeval` package directly because the user explicitly requested “no tricks”.
2. During this session, the direct DeepEval import path was shown to be expensive because it pulls in a very large package tree.
3. The OpenAI judge transport was being actively refined during smoke testing.
4. A one-task live smoke succeeded earlier under a compatibility path, but after reverting to “actual DeepEval package only”, the next operator should re-verify end-to-end judge behavior on the target machine.
5. Anthropic direct HTTPS smoke test still needs verification.

## What Should Not Be Changed Casually

- Task prompts, assertions, judge prompts, and images must stay aligned
- Structural score semantics must remain deterministic from `assertions.json`
- Editing tasks must preserve source/reference/candidate image ordering
- The shared judge contract should stay visible in `shared_judge_contract.txt`
- Avoid hiding important benchmark behavior in inline Python strings

## Recommended Next Steps

1. Run a 1-task and 2-task judge smoke test on the target machine with actual DeepEval imports enabled by default.
2. Verify OpenAI and Anthropic judge transport behavior separately.
3. If DeepEval package startup is still too brittle on real user machines, consider documenting that explicitly or revisiting the runtime design.
4. Add a lightweight operator-facing troubleshooting section to `README.md`.
5. If needed, add a dedicated `PROJECT_STATUS.md` refresh after every major benchmark/eval change.

## Last Confirmed Git State In This Session

The repo was committed and pushed multiple times during this session.

Latest confirmed commit before this handoff-doc request:

- `5e828f7` — `Refine multimodal judge pipeline`

Any operator continuing from here should still run:

```bash
git status
git log --oneline -n 5
```

before starting new work.
