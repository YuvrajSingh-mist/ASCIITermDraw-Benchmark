# TermDraw-Bench

TermDraw-Bench is a benchmark for evaluating whether language models can
generate and edit structured ASCII diagrams.

It ships as a normal GitHub-style repository with:

- `80` tasks across `4` categories
- checked-in `tasks/` and `oneshot/` assets
- Fireworks-based generation scripts
- assertion scoring plus a VLM judge
- a website under `website/`

## Quick Start

The benchmark already ships prebuilt in this repository. You do not need to
generate the tasks yourself.

To run models against it locally:

```bash
uv sync
cp .env.example .env
# put your Fireworks key in .env
```

Then use one of these:

```bash
uv run smoke --model accounts/fireworks/models/qwen3p7-plus --outputs outputs/smoke
uv run run-model --model accounts/fireworks/models/your-model --outputs outputs/my-run
uv run eval --outputs outputs/my-run --results results.csv
uv run judge --model accounts/fireworks/models/your-judge-model --outputs outputs/my-run --results judge_results.csv
```

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
├── oneshot/
├── tasks/
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
  --oneshot oneshot/ \
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
  --oneshot oneshot/ \
  --reasoning-effort none \
  --sample-count 5 \
  --seed 7
```

This runs synchronous requests and writes one `{task_id}.txt` per selected task
plus `outputs/smoke/manifest.json`.

Run L1 scoring:

```bash
uv run eval \
  --outputs outputs/qwen2.5-7b/ \
  --tasks tasks/ \
  --results results_qwen2.5-7b.csv
```

Run structured-output judging:

```bash
uv run judge \
  --model accounts/fireworks/models/your-judge-model \
  --tasks tasks/ \
  --outputs outputs/qwen2.5-7b/ \
  --results results_qwen2.5-7b.csv
```

This uses the Pydantic / Instructor path and stores parsed JSON judgments in
`outputs/.../judge_json/`. The judge now returns `structural_score`,
`semantics_score`, and `score`, where `score = structural_score + semantics_score`.

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
