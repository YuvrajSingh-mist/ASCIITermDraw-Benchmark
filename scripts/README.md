# Scripts

This directory is organized so the top level stays reserved for stable CLI
entrypoints, with workflow-specific subdirectories used where that makes the
repository easier to navigate.

## Layout

- `scripts/*.py`: core command implementations exposed through `uv run ...`
- `scripts/benchmark/`: internal maintainer modules and canonical benchmark source data
- `scripts/judge/`: VLM judging entrypoints
- `scripts/lib/`: shared Python helpers used by multiple commands
- `scripts/rendered/`: ASCII-to-PNG rendering entrypoints and renderer implementation

## Stability

If you add a new reusable helper, prefer `scripts/lib/`.
If you add a new main workflow command, keep it at the top level of `scripts/` unless it clearly belongs to a focused sub-area such as `judge/` or `rendered/`.
If you add a renderer backend, place it under `scripts/rendered/`.
The checked-in `tasks/` dataset is the intended user-facing artifact. The `scripts/benchmark/` code exists as internal maintainer context, not as part of the normal dataset usage flow.
