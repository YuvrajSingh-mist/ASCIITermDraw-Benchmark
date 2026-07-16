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
The benchmark source-of-truth generation code lives under `scripts/benchmark/`. The published dataset can be distributed separately from the repo, so avoid coupling ordinary user workflows to rebuilding it locally.
