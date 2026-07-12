# Contributing

## Principles

- Keep task data deterministic and text-based.
- Preserve the existing directory and file naming scheme.
- Keep task directories nested by named category, for example
  `tasks/network-topology-diagrams/2.14/`.
- Treat `generate_benchmark.py` as the source of truth for generated content.
- Regenerate benchmark assets after editing task definitions.
- Never commit real API keys or local credential files.

## Making Changes

1. Update `generate_benchmark.py` if the benchmark content changes.
2. Regenerate files:

```bash
.venv/bin/python generate_benchmark.py
```

3. Render PNG assets:

```bash
npm install
npx playwright install chromium
.venv/bin/python scripts/render_all.py
```

4. Verify counts:

```bash
make verify
```

5. If you are validating inference changes, use Fireworks credentials instead
   of local `vllm`:

```bash
export FIREWORKS_API_KEY=...
export FIREWORKS_ACCOUNT_ID=...
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
