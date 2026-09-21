#!/usr/bin/env bash
set -euo pipefail

echo "== Python format =="
uv run ruff format --check .

echo "== Python lint =="
uv run ruff check .

echo "== Python types =="
uv run pyright

echo "== Python tests =="
uv run pytest

if find . -name Cargo.toml -not -path './target/*' -print -quit | grep -q .; then
    echo "== Rust format =="
    cargo fmt --check

    echo "== Rust clippy =="
    cargo clippy --all-targets --all-features -- -D warnings

    echo "== Rust tests =="
    cargo test
fi

echo "All checks passed."
