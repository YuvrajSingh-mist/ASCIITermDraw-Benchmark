# TermDraw-Bench

TermDraw-Bench is a benchmark for evaluating whether language models can
generate and edit structured ASCII diagrams.

It ships as a normal GitHub-style repository with:

- `80` private tasks across `4` categories (`tasks/`, not distributed publicly)
- `12` public example tasks (`public_dataset/`) — same format, fully runnable,
  safe to look at
- Fireworks-based generation (model responses + rendered PNGs only —
  Fireworks is not used for judging)
- a DeepEval `BaseMetric` judge against OpenAI/Anthropic — the only scoring
  path (`geval_*` scores); there is no separate deterministic/text-heuristic
  scoring step
- a website under `website/`

## Quick Start

```bash
uv sync
cp .env.example .env
# put your Fireworks / OpenAI / Anthropic keys in .env
```

Rendering ASCII diagrams to PNG uses Node + Playwright. See `DEVELOPER.md`
(local-only, not tracked in this repo) for setup; once set up:

```bash
uv run python -m scripts.rendered.render_all
```

`--model` must be a model actually deployed on your Fireworks account —
placeholder-looking names (`your-model`, `qwen3-vl-8b-instruct`, etc.) will
404. `qwen3p7-plus` is a real, currently-working example; verify your own
account's available models before a large run.

## Public Dataset

`tasks/` (the real 80-task test set) is **not** checked into this repository
— see `.gitignore` — and is not publicly distributed, since it's the
benchmark's held-out evaluation set. Access is maintainer-controlled; this
README does not document how to obtain it.

`public_dataset/` exists so anyone can see the task format and actually run
the tooling without that access. It contains 12 hand-authored tasks — one
`easy`, one `medium`, one `hard` per category — laid out identically to a
real task (`<category>/<difficulty>/<task_id>/`, task ids `0.1`–`0.12`), and
is a genuine drop-in `--tasks` target for both scripts below, not just a
documentation sample:

```bash
uv run run-model \
  --model accounts/fireworks/models/qwen3p7-plus \
  --tasks public_dataset \
  --outputs outputs/public_demo

uv run judge-geval \
  --provider openai \
  --model gpt-5.4 \
  --tasks public_dataset \
  --outputs outputs/public_demo/qwen3p7-plus \
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
(`.1`–`.10` easy, `.11`–`.15` medium, `.16`–`.20` hard); `public_dataset/`
uses one task per bucket (`0.1`–`0.12`).

## Repository Layout

```text
.
├── tasks/                  # private, generated, not checked in — see Public Dataset
│   ├── box-layout-basics/
│   ├── network-topology-diagrams/
│   ├── diagram-editing/
│   └── software-architecture-diagrams/
├── public_dataset/         # public, checked in — 12 runnable example tasks
│   ├── box-layout-basics/
│   ├── network-topology-diagrams/
│   ├── diagram-editing/
│   └── software-architecture-diagrams/
├── scripts/
│   ├── benchmark/      # internal maintainer tooling + canonical source data
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
  --model accounts/fireworks/models/your-model \
  --tasks tasks/ \
  --outputs outputs/ \
  --reasoning-effort none \
  --network-retries 5
```

Category 3 (`diagram-editing`) requests attach `source.png` as multimodal
image input; other categories are text-only. Reasoning is disabled by
default (`reasoning_effort=none`). Generation cost/token usage is written to
`manifest.json` under the output directory when known pricing is available
for the model (built-in default for `qwen3p7-plus`; otherwise pass
`--input-price-per-million`/`--output-price-per-million`).

For a quick smoke test instead of a full run:

```bash
uv run smoke \
  --model accounts/fireworks/models/your-model \
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
output PNGs — Fireworks is used purely for generation, not judging, and this
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

- **`RuntimeError: No task directories selected.`** — the `--tasks`
  directory is empty, missing, or has no `<category>/<difficulty>/<id>/`
  subdirectories matching a task-id pattern (`\d+\.\d+`). Try
  `--tasks public_dataset` first to confirm the pipeline itself works.
- **Playwright / rendering errors** — see `DEVELOPER.md`.
- **Fireworks `HTTP 404: Model not found, inaccessible, and/or not
  deployed`** — the `--model` value isn't deployed on your Fireworks
  account. Confirm the exact model path (`accounts/fireworks/models/...`)
  from your Fireworks dashboard rather than reusing an example from this
  README verbatim.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository conventions and contribution guidance.

## Website

The benchmark website lives in `website/` (`index.html`, `pages/` for
secondary pages, `assets/` for CSS/JS/generated data, `tools/` for the site
data build script) and is set up for GitHub Pages.

To preview locally:

```bash
node website/tools/build_site_data.mjs
python3 -m http.server 8000 -d website
```

`build_site_data.mjs` regenerates `website/assets/data/site_data.json` from
the real `tasks/` tree (private task metadata — prompts and previews for the
task browser) and `public_dataset/` (copies the 12 public reference PNGs
into `website/assets/img/public-dataset/` and embeds their trimmed prompts).
Re-run it after editing either task tree.

Deployment is automatic via
[`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml):
on every push to `master`, GitHub Actions rebuilds `site_data.json` and
deploys `website/` as the Pages artifact. The site uses repo-relative asset
paths, so it works when published under a repository subpath.

To enable it in GitHub:

1. Push this repository to GitHub.
2. In `Settings -> Pages`, set `Source` to `GitHub Actions`.
3. Push to `master` or run the `Deploy Website` workflow manually.

## Notes

- The benchmark content was generated from the instructions in
  `termdraw_benchmark_spec.md`.
- A project license has not been added yet. For a published benchmark, choose
  a license explicitly before distribution.
