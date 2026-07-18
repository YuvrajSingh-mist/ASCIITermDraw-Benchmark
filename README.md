# TermDraw-Bench

TermDraw-Bench is a benchmark for evaluating whether language models can
generate and edit structured ASCII diagrams.

It ships as a normal GitHub-style repository with:

- `80` private tasks across `4` categories (`tasks/`, not distributed publicly)
- `12` public example tasks (same format, fully runnable, safe to look at)
  published on [Hugging Face](https://huggingface.co/datasets/YuvrajSingh9886/asciitermdraw-bench-public)
  rather than bundled in this repository
- Together AI-based generation (model responses and rendered PNGs only;
  Together is not used for judging)
- a DeepEval `BaseMetric` judge against OpenAI/Anthropic, the only scoring
  path (`geval_*` scores); there is no separate deterministic/text-heuristic
  scoring step
- a website under `website/`

## Quick Start

```bash
uv sync
cp .env.example .env
# put your Together AI / OpenAI / Anthropic keys in .env
```

Rendering ASCII diagrams to PNG uses Node + Playwright. See `DEVELOPER.md`
(local-only, not tracked in this repo) for setup; once set up:

```bash
uv run python -m scripts.rendered.render_all
```

`--model` must be a valid Together AI model slug (e.g. `Qwen/Qwen3.7-Plus`,
`MiniMaxAI/MiniMax-M3`, `moonshotai/Kimi-K2.6`); check
[together.ai/models](https://www.together.ai/models) for the exact slug
before a large run, since placeholder-looking names will 404.

## Public Dataset

`tasks/` (the real 80-task test set) is **not** checked into this repository
— see `.gitignore` — and is not publicly distributed, since it's the
benchmark's held-out evaluation set. Access is maintainer-controlled; this
README does not document how to obtain it.

The [public dataset on Hugging Face](https://huggingface.co/datasets/YuvrajSingh9886/asciitermdraw-bench-public)
exists so anyone can see the task format and actually run the tooling
without that access — browse it directly, or download it locally as a
genuine drop-in `--tasks` target for both scripts below (it contains 12
hand-authored tasks — one `easy`, one `medium`, one `hard` per category —
laid out identically to a real task, `<category>/<difficulty>/<task_id>/`,
task ids `0.1`–`0.12`):

```bash
huggingface-cli download YuvrajSingh9886/asciitermdraw-bench-public \
  --repo-type dataset --local-dir public_dataset

uv run run-model \
  --model Qwen/Qwen3.7-Plus \
  --tasks public_dataset \
  --outputs outputs/public_demo

uv run judge-geval \
  --provider openai \
  --model gpt-5.4 \
  --tasks public_dataset \
  --outputs outputs/public_demo/qwen3.7-plus \
  --results outputs/public_demo/results.csv \
  --num-judgments 5
```

This is the fastest way to confirm your environment and API keys are wired
up correctly before requesting access to the private task set — generating
and judging all 12 public tasks costs well under $1. Each public task has
the same file layout described under "What Is In The Benchmark" below.

## What Is In The Benchmark

- Category 1 (`box-layout-basics`): box drawing and ASCII layout basics
- Category 2 (`network-topology-diagrams`): network, systems, and cluster
  topology diagrams
- Category 3 (`diagram-editing`): diagram editing tasks with source and
  target diagrams
- Category 4 (`software-architecture-diagrams`): canonical software
  architecture diagrams

Each task directory contains:

- `prompt.txt`
- `reference.ascii`
- `reference.png`
- `assertions.json`
- `vlm_judge_prompt.txt`

Category 3 (editing) tasks also contain `source.ascii` and `source.png`.

Within each category, tasks are organized by difficulty: `easy/`, `medium/`,
`hard/`. In the private set, difficulty buckets map to task-id ranges
(`.1`–`.10` easy, `.11`–`.15` medium, `.16`–`.20` hard); the public dataset
uses one task per bucket (`0.1`–`0.12`).

## Repository Layout

```text
.
├── tasks/                  # private, generated, not checked in — see Public Dataset
│   ├── box-layout-basics/
│   ├── network-topology-diagrams/
│   ├── diagram-editing/
│   └── software-architecture-diagrams/
├── scripts/
│   ├── judge/          # DeepEval BaseMetric judge (judge-geval)
│   ├── rendered/       # ASCII -> PNG renderer
│   ├── lib/            # shared helpers
│   ├── run_model.py
│   └── smoke_generate.py
├── website/             # static site; see Website section below
├── pyproject.toml
├── uv.lock
└── README.md
```

## Generating and Judging

`--tasks` defaults to `tasks/`; pass `--tasks public_dataset` to run against
the public set instead (see Public Dataset above), or point it at a private
checkout of `tasks/` for the real benchmark.

```bash
uv run run-model \
  --model Qwen/Qwen3.7-Plus \
  --tasks tasks/ \
  --outputs outputs/ \
  --reasoning-effort none \
  --network-retries 5
```

Category 3 (`diagram-editing`) requests attach `source.png` as multimodal
image input; other categories are text-only. Reasoning is disabled by
default (`reasoning_effort=none`), sent explicitly as
`{"reasoning": {"enabled": false}}`, since these are hybrid-reasoning models
that reason by default even with no `reasoning` field at all. Every request
is sent with `stream: true` and reassembled into a normal response, since
some Together model deployments reject non-streaming requests outright.
Together does not report a per-request dollar cost, so generation
cost/token usage written to `manifest.json` under the output directory is
always computed from the built-in per-model price defaults (`qwen3.7-plus`,
`minimax-m3`, `kimi-k2.6`) or an explicit `--input-price-per-million`/
`--output-price-per-million`.

For a quick smoke test instead of a full run:

```bash
uv run smoke \
  --model Qwen/Qwen3.7-Plus \
  --tasks tasks/ \
  --outputs outputs/smoke \
  --sample-count 5 \
  --seed 7
```

This writes generations mirroring the `tasks/` layout — one
`<category>/<difficulty>/<task_id>/{task_id}.txt` (plus a rendered `.png`)
per selected task — and `outputs/<run>/<model-name>/manifest.json` (the last
segment of `--model` is auto-appended to `--outputs`).

Judging is OpenAI/Anthropic only, via DeepEval `BaseMetric` against rendered
output PNGs. Together AI is used purely for generation, not judging, and this
is the only scoring path in the repo:

```bash
uv run judge-geval \
  --provider openai \
  --model gpt-5.4 \
  --tasks tasks/ \
  --outputs outputs/your-model \
  --results results_your-model.csv \
  --num-judgments 5
```

For Anthropic, pass `--provider anthropic --model claude-sonnet-5`.
`judge-geval` skips any task without a matching candidate output rather than
failing — generate first, then judge. Add `--task-id 1.10` to judge a single
task, or `--dry-run` to verify artifact wiring without making provider
calls.

If a run dies partway through (rate limit, quota, crash), rerun the exact
same command with `--resume` added: it skips any task that already has a
`gval/result.json` under `--outputs` and only judges what's left, instead of
re-judging the whole task set from scratch.

`--num-judgments N` (default `5`) repeats the judge call N times per task
(independent API calls, not cached) and reports the mean and population
stdev across rounds, to average out judge-model noise — this is distinct
from generation variance. `--judge-temperature` optionally overrides the
judge model's sampling temperature (otherwise left at the provider's
default) if you want to deliberately widen the spread across rounds.

Results are written with `geval_structural_score`, `geval_semantics_score`,
`geval_score` (`= geval_structural_score + geval_semantics_score`),
`geval_structural_stdev`, `geval_semantics_stdev`, `geval_num_judgments`, and
token/cost columns (`geval_input_tokens`, `geval_output_tokens`,
`geval_total_tokens`, `geval_cost_usd`). `gpt-5.4` and `claude-sonnet-5` have
built-in pricing defaults; for other judge models pass
`--input-price-per-million`/`--output-price-per-million`.

## Troubleshooting

- **`RuntimeError: No task directories selected.`**: the `--tasks`
  directory is empty, missing, or has no `<category>/<difficulty>/<id>/`
  subdirectories matching a task-id pattern (`\d+\.\d+`). Try
  `--tasks public_dataset` first to confirm the pipeline itself works.
- **Playwright / rendering errors**: see `DEVELOPER.md`.
- **Together `HTTP 404: Unable to access model <model>`**: the
  `--model` value isn't a real Together AI model slug. Confirm the exact
  slug (e.g. `Qwen/Qwen3.7-Plus`, not `qwen3p7-plus`) at
  [together.ai/models](https://www.together.ai/models) rather than reusing
  an example from this README verbatim.
- **`HTTP 402: Insufficient credits`**: the Together account has run out
  of balance. Check remaining credits before a large run; a partial
  generation run can be resumed for just the missing task ids via
  `--task-ids`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository conventions and contribution guidance.
the `Deploy Website` workflow manually.

