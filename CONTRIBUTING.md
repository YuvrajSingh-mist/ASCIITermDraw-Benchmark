# Contributing

## Principles

- Keep task data deterministic and text-based.
- Preserve the existing directory and file naming scheme.
- Keep task directories nested by named category, for example
  `tasks/network-topology-diagrams/medium/2.14/`.
- Treat `scripts/benchmark/data/` as the canonical source for generated content.
- Regenerate benchmark assets after editing task definitions.
- Never commit real API keys or local credential files.

## Making Changes

1. Update the benchmark source data under `scripts/benchmark/data/` if the
   benchmark content changes.
2. Regenerate files:

```bash
uv run python -m scripts.benchmark.build
```

3. Render PNG assets:

```bash
uv sync
npx playwright install chromium
uv run python scripts/rendered/render_all.py
```

4. Verify counts:

```bash
uv run python - <<'PY'
from pathlib import Path
tasks = Path("tasks")
print("Task categories:", len([p for p in tasks.iterdir() if p.is_dir()]))
print("Task directories:", len([p for p in tasks.rglob("*") if p.is_dir() and p.name.count(".") == 1]))
print("prompt.txt files:", len(list(tasks.rglob("prompt.txt"))))
print("reference.ascii:", len(list(tasks.rglob("reference.ascii"))))
print("assertions.json:", len(list(tasks.rglob("assertions.json"))))
print("vlm_judge_prompt:", len(list(tasks.rglob("vlm_judge_prompt.txt"))))
print("source.ascii:", len(list(tasks.rglob("source.ascii"))))
PY
```

5. If you are validating inference changes, use Fireworks credentials instead
   of local `vllm`. Put them in `.env` or `.env.local` rather than exporting
   them ad hoc:

```bash
FIREWORKS_API_KEY=...
FIREWORKS_ACCOUNT_ID=...
```

## Task Authoring Conventions

- Use ASCII-only diagrams.
- Keep labels stable across prompt, reference, assertions, and judge prompt.
- Ensure `assertions.json` stays aligned with the intended structure.
- For editing tasks, preserve unchanged source elements unless the prompt says
  otherwise.
- Keep rendered PNGs diagram-only. Do not include task instructions or extra
  prose inside benchmark image assets.

## Pull Request Expectations

- Explain whether the change affects benchmark content, evaluation logic, or
  documentation.
- Mention if rendered `.png` assets were regenerated.
- Include any known limitations or follow-up work.
