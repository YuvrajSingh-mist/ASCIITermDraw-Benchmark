# Scripts

This directory is organized so the top level stays reserved for stable CLI
entrypoints that are referenced from the README and GitHub workflows.

## Layout

- `scripts/*.py`: user-facing commands such as generation, rendering, eval, and judging
- `scripts/lib/`: shared Python helpers used by multiple commands
- `scripts/renderers/`: renderer implementations and renderer-specific assets
- `scripts/examples/`: sample and exploratory renderer scripts that are not part of the main benchmark workflow

## Stability

If you add a new reusable helper, prefer `scripts/lib/`.
If you add a new main workflow command, keep it at the top level of `scripts/`.
If you add a renderer backend or demo, place it under `scripts/renderers/` or `scripts/examples/`.
