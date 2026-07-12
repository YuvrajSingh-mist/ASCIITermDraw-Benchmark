# TermDraw-Bench

TermDraw-Bench is a benchmark for evaluating whether language models can
generate and edit structured ASCII diagrams. It contains 80 tasks across
four categories:

- Category 1: Box drawing and ASCII layout basics
- Category 2: Network, systems, and cluster topology diagrams
- Category 3: Diagram editing tasks with source and target diagrams
- Category 4: Canonical software architecture diagrams

Each task directory includes machine-readable assertions, a reference ASCII
diagram, and a task-specific VLM judge prompt. Category 3 tasks also include
the source diagram the model is expected to modify.

## Repository Layout

```text
.
├── .github/
│   └── workflows/
│       └── deploy-pages.yml
├── generate_benchmark.py
├── oneshot/
│   ├── c1_example.txt
│   ├── c2_example.txt
│   ├── c3_example.txt
│   └── c4_example.txt
├── scripts/
│   ├── eval.py
│   ├── examples/
│   ├── lib/
│   ├── render.py
│   ├── render_all.py
│   ├── renderers/
│   ├── run_model.py
│   ├── run_vlm_judge_instructor.py
│   ├── smoke_generate.py
│   └── run_vlm_judge.py
├── tasks/
│   ├── box-layout-basics/
│   │   ├── 1.1/
│   │   └── ...
│   ├── diagram-editing/
│   ├── network-topology-diagrams/
│   ├── ...
│   └── software-architecture-diagrams/
│       └── 4.15/
├── website/
│   ├── app.js
│   ├── build_site_data.mjs
│   ├── build_site_data.py
│   ├── index.html
│   └── style.css
└── termdraw_benchmark_spec.md
```

## Task Format

Every task contains:

- `prompt.txt`: the instruction shown to the model
- `reference.ascii`: the target ASCII diagram
- `assertions.json`: structural checks for L1 scoring
- `vlm_judge_prompt.txt`: task-specific prompt for L2 judging

Category 3 tasks also contain:

- `source.ascii`: the starting diagram before editing

After rendering, `.png` companions are produced for each `.ascii` file.
These PNGs should contain the diagram only, not the surrounding task prompt.

## Quick Start

1. Install dependencies:

```bash
uv venv
uv sync
npm install
npx playwright install chromium
cp .env.example .env.local
```

2. Configure Fireworks credentials:

```bash
cp .env.example .env
# Then edit .env with your real Fireworks values.
```

All scripts auto-load `.env.local` first and then `.env`, so you do not need
to `export` credentials in every shell. Keep real credentials in ignored local
files; do not commit them to a public repository.

3. Regenerate repository assets:

```bash
.venv/bin/python generate_benchmark.py
```

4. Render PNGs:

```bash
.venv/bin/python scripts/render_all.py
```

5. Verify expected counts:

```bash
make verify
```

## Working Commands

The commands below are the intended published workflow for the repository.

Setup:

```bash
uv venv
uv sync
npm install
npx playwright install chromium
cp .env.example .env.local
```

Then put your Fireworks credentials in `.env.local` or `.env`:

```bash
FIREWORKS_API_KEY=...
FIREWORKS_ACCOUNT_ID=...
```

Render all task diagrams to PNG with Playwright:

```bash
.venv/bin/python scripts/render_all.py
```

Regenerate the benchmark tree from source:

```bash
.venv/bin/python generate_benchmark.py
```

Verified Fireworks smoke test with reasoning disabled:

```bash
python3 scripts/smoke_generate.py \
  --model accounts/fireworks/models/qwen3p7-plus \
  --tasks tasks/ \
  --outputs outputs/smoke-qwen3p7-plus/ \
  --oneshot oneshot/ \
  --sample-count 5 \
  --seed 7 \
  --reasoning-effort none \
  --network-retries 5
```

Full batch generation run:

```bash
python3 scripts/run_model.py \
  --model accounts/fireworks/models/your-vision-model \
  --tasks tasks/ \
  --outputs outputs/your-run/ \
  --oneshot oneshot/ \
  --reasoning-effort none \
  --network-retries 5
```

L1 structural scoring:

```bash
python3 scripts/eval.py \
  --outputs outputs/your-run/ \
  --tasks tasks/ \
  --results results_your_run.csv
```

Fireworks structured judge run:

```bash
python3 scripts/run_vlm_judge.py \
  --model accounts/fireworks/models/your-judge-model \
  --tasks tasks/ \
  --outputs outputs/your-run/ \
  --results results_your_run.csv \
  --network-retries 5
```

Instructor/Pydantic judge variant:

```bash
python3 scripts/run_vlm_judge_instructor.py \
  --model accounts/fireworks/models/your-judge-model \
  --tasks tasks/ \
  --outputs outputs/your-run/ \
  --results results_your_run.csv
```

Build website task metadata:

```bash
node website/build_site_data.mjs
```

Preview the website locally:

```bash
python3 -m http.server 8000 -d website
```

Then open `http://localhost:8000`.

Push to GitHub and publish with GitHub Pages:

```bash
git init
git branch -M main
git add .
git commit -m "Initial benchmark release"
git remote add origin git@github.com:YOUR_ORG/ASCIITermDraw-Benchmark.git
git push -u origin main
```

After push, enable GitHub Pages for GitHub Actions in repository settings. The
included workflow at `.github/workflows/deploy-pages.yml` will publish the
`website/` directory.

## Running Evaluation

Run generation batch inference:

```bash
python3 scripts/run_model.py \
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

For a quick smoke test instead of all 80 tasks:

```bash
python3 scripts/smoke_generate.py \
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
python3 scripts/eval.py \
  --outputs outputs/qwen2.5-7b/ \
  --tasks tasks/ \
  --results results_qwen2.5-7b.csv
```

Run Fireworks structured-output judging:

```bash
python3 scripts/run_vlm_judge.py \
  --model accounts/fireworks/models/your-judge-model \
  --tasks tasks/ \
  --outputs outputs/qwen2.5-7b/ \
  --results results_qwen2.5-7b.csv \
  --network-retries 5
```

This reads each task's `vlm_judge_prompt.txt`, submits a Fireworks Batch API
job, and stores parsed JSON judgments in `outputs/.../judge_json/`.

For smaller non-batch judging runs, there is also an Instructor-based option:

```bash
python3 scripts/run_vlm_judge_instructor.py \
  --model accounts/fireworks/models/your-judge-model \
  --tasks tasks/ \
  --outputs outputs/qwen2.5-7b/ \
  --results results_qwen2.5-7b.csv
```

## Reproducibility

`generate_benchmark.py` is the canonical source for regenerating the task
directories and support scripts in this repository. If you modify the benchmark
content, rerun the generator and re-render the PNG assets before publishing
changes. Rendering is Playwright-based and is intended to capture only the
ASCII diagram artifact. Inference is Fireworks-based: generation uses the
Batch API and L2 judging uses structured JSON outputs.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for repository conventions and contribution guidance.

## Notes

- The benchmark content was generated from the instructions in
  `termdraw_benchmark_spec.md`.
- A project license has not been added yet. For a published benchmark, choose
  a license explicitly before distribution.
