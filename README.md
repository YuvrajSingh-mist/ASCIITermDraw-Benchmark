# TermDraw-Bench

TermDraw-Bench is a benchmark for evaluating whether language models can
generate and edit structured ASCII diagrams.

It ships as a normal GitHub-style repository with:

- `80` tasks across `4` categories
- a generated `tasks/` tree (not distributed publicly — it's the test set)
- Fireworks-based generation (model responses + rendered PNGs only —
  Fireworks is not used for judging)
- assertion scoring plus a DeepEval `BaseMetric` judge against OpenAI/Anthropic
- a website under `website/`

## Quick Start

`tasks/` is **not** checked into this repository (see `.gitignore`) and is
not publicly distributed — it's the benchmark's test set, generated from
`scripts/benchmark/data/*.json`. Access is maintainer-controlled; this README
does not document how to obtain it. If you're running this benchmark and
don't already have `tasks/` in place, ask the maintainer.

```bash
uv sync
cp .env.example .env
# put your Fireworks / OpenAI / Anthropic keys in .env
```

### 1. Render reference PNGs

Rendering ASCII diagrams to PNG uses Node + Playwright. See `DEVELOPER.md`
(local-only, not tracked in this repo) for setup; once set up:

```bash
uv run python -m scripts.rendered.render_all
```

### 2. Generate and judge

```bash
uv run smoke --model accounts/fireworks/models/qwen3p7-plus --outputs outputs/smoke
uv run run-model --model accounts/fireworks/models/your-model --outputs outputs/my-run
uv run eval --outputs outputs/my-run --results results.csv
uv run judge-geval --provider openai --model gpt-5.4 --tasks tasks --outputs outputs/my-run --results outputs/geval_results.csv
```

`--model` must be a model actually deployed on your Fireworks account —
placeholder-looking names (`your-model`, `qwen3-vl-8b-instruct`, etc.) will
404. `qwen3p7-plus` above is a real, currently-working example; verify your
own account's available models before a large run.

That is the intended user-facing surface. The lower-level Python scripts still
exist, but most people should not need to call them directly.

## What Is In The Benchmark

- Category 1: box drawing and ASCII layout basics
- Category 2: network, systems, and cluster topology diagrams
- Category 3: diagram editing tasks with source and target diagrams
- Category 4: canonical software architecture diagrams

Each task directory contains:

- `prompt.txt`
- `reference.ascii`
- `reference.png`
- `assertions.json`
- `vlm_judge_prompt.txt`

Category 3 tasks also contain:

- `source.ascii`
- `source.png`

## Repository Layout

```text
.
├── tasks/                  # generated, not checked in — see Quick Start
│   ├── box-layout-basics/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   ├── network-topology-diagrams/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   ├── diagram-editing/
│   │   ├── easy/
│   │   ├── medium/
│   │   └── hard/
│   └── software-architecture-diagrams/
│       ├── easy/
│       ├── medium/
│       └── hard/
├── scripts/
│   ├── benchmark/      # internal maintainer tooling + canonical source data
│   ├── judge/          # VLM judge entrypoint
│   ├── rendered/       # ASCII -> PNG renderer
│   ├── lib/            # shared helpers
│   ├── run_model.py
│   ├── smoke_generate.py
│   └── eval.py
├── website/
├── pyproject.toml
├── uv.lock
└── README.md
```

## Running Evaluation

Run full generation:

```bash
uv run run-model \
  --model accounts/fireworks/models/your-vision-model \
  --tasks tasks/ \
  --outputs outputs/qwen2.5-7b/ \
  --reasoning-effort none \
  --network-retries 5
```

Category 3 requests attach `source.png` as multimodal image input. The other
categories remain text-only. Thinking/reasoning is disabled by default during
generation with `reasoning_effort=none`.

Within each category folder, tasks are organized by difficulty:

- `easy/`: tasks `.1` to `.10`
- `medium/`: tasks `.11` to `.15`
- `hard/`: tasks `.16` to `.20`

For a quick smoke test instead of all 80 tasks:

```bash
uv run smoke \
  --model accounts/fireworks/models/your-vision-model \
  --tasks tasks/ \
  --outputs outputs/smoke/ \
  --reasoning-effort none \
  --sample-count 5 \
  --seed 7
```

This runs synchronous requests and writes generations mirroring the
`tasks/` layout — one `<category>/<difficulty>/<task_id>/{task_id}.txt`
(and a rendered `.png` alongside it) per selected task — plus
`outputs/smoke/manifest.json`.

Run L1 scoring:

```bash
uv run eval \
  --outputs outputs/qwen2.5-7b/ \
  --tasks tasks/ \
  --results results_qwen2.5-7b.csv
```

Judging is OpenAI/Anthropic only, via DeepEval `BaseMetric` (real `deepeval`
package import) against rendered output PNGs — Fireworks is used purely for
generation, not judging:

```bash
uv run judge-geval \
  --provider openai \
  --model gpt-5.4 \
  --tasks tasks/ \
  --outputs outputs/qwen2.5-7b/ \
  --results results_qwen2.5-7b.csv
```

For Anthropic:

```bash
uv run judge-geval \
  --provider anthropic \
  --model claude-sonnet-4-5 \
  --tasks tasks/ \
  --outputs outputs/qwen2.5-7b/ \
  --results results_qwen2.5-7b.csv
```

`judge-geval` skips any task without a matching candidate output (at
`outputs/<category>/<difficulty>/<task_id>/<task_id>.txt`, mirroring `tasks/`)
rather than failing — generate first, then judge.
While iterating on the judge itself you can equivalently run the live source
tree directly with `uv run python -m scripts.judge.run_geval_judge ...`
using the same flags.

Add `--task-id 1.10` to judge a single task, or `--dry-run` to verify
artifact wiring (candidate rendering, image assembly) without making any
provider calls.

Results are written with `geval_structural_score`, `geval_semantics_score`,
and `geval_score` columns, where
`geval_score = geval_structural_score + geval_semantics_score`.

## Troubleshooting

- **`RuntimeError: No task directories selected.`** — `tasks/` is empty or
  missing. Make sure the task set has been placed at `tasks/` (see Quick
  Start) before running any generation, eval, or judge command.
- **Playwright / rendering errors** — see `DEVELOPER.md`.
- **Fireworks `HTTP 404: Model not found, inaccessible, and/or not
  deployed`** — the `--model` value isn't deployed on your Fireworks
  account. Confirm the exact model path (`accounts/fireworks/models/...`)
  from your Fireworks dashboard rather than reusing an example from this
  README verbatim.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository conventions and contribution guidance.

## Website Publishing

The benchmark website lives in `website/` and is set up for GitHub Pages.

- The deployment workflow is [`.github/workflows/deploy-pages.yml`](/Users/yuvrajsingh9886/Desktop/ASCIITermDraw-Benchmark/.github/workflows/deploy-pages.yml).
- On every push to `main`, GitHub Actions rebuilds `website/assets/data/site_data.json` from the real `tasks/` tree and deploys the `website/` directory as the Pages artifact.
- The site uses repo-relative asset paths, so it works when published under the repository subpath on GitHub Pages.

To enable it in GitHub:

1. Push this repository to GitHub.
2. In `Settings -> Pages`, set `Source` to `GitHub Actions`.
3. Push to `main` or run the `Deploy Website` workflow manually.

## Notes

- The benchmark content was generated from the instructions in
  `termdraw_benchmark_spec.md`.
- A project license has not been added yet. For a published benchmark, choose
  a license explicitly before distribution.
