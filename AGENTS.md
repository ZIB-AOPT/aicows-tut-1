# Agent instructions

## Goal

Make small, reviewable changes and verify them before declaring a task complete.

## Before editing

- Read the relevant source files and tests first.
- Inspect existing conventions before introducing new patterns.
- Prefer the smallest change that solves the requested problem.

## Python

Use the project environment through `uv`.

After changing Python code, run:

    uv run ruff format --check .
    uv run ruff check .
    uv run pyright
    uv run pytest

Do not install Python packages globally.

If dependencies change, update `pyproject.toml` and `uv.lock` intentionally.

## Rust

After changing Rust code, run:

    cargo fmt --check
    cargo clippy --all-targets --all-features -- -D warnings
    cargo test

Treat Clippy warnings as failures unless the project explicitly documents an exception.

## Gurobi

- Use `gurobipy` from the project environment.
- Never copy, inspect unnecessarily, modify, or commit the user's Gurobi license file.
- Do not add license credentials to source code, tests, notebooks, logs, or configuration committed to Git.
- Keep examples deterministic where practical.
- Check optimization status before reading solution values.
- Add tests for model behavior when changing optimization logic.

## Git and safety

- Inspect `git diff` before finishing.
- Do not commit or push unless explicitly requested.
- Do not rewrite Git history unless explicitly requested.
- Do not run destructive filesystem or Git commands unless explicitly requested.
- Do not use `sudo`.
- Never expose secrets, tokens, API keys, or license credentials.

## Completion

Before finishing, run:

    ./scripts/check.sh

A task is complete only when the relevant formatter, linter, type checker/compiler, and tests pass.
