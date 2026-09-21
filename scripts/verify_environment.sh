#!/usr/bin/env bash
set -euo pipefail

commands=(
  git
  opencode
  rg
  fd
  jq
  rustup
  rustc
  cargo
  rustfmt
  uv
)

failed=0

for cmd in "${commands[@]}"; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "%-12s OK  %s\n" "$cmd" "$(command -v "$cmd")"
  else
    printf "%-12s MISSING\n" "$cmd"
    failed=1
  fi
done

if command -v cargo >/dev/null 2>&1; then
  if cargo clippy --version >/dev/null 2>&1; then
    echo "clippy       OK"
  else
    echo "clippy       MISSING"
    failed=1
  fi
fi

if command -v uv >/dev/null 2>&1; then
  echo
  echo "== Project Python tools =="
  uv run python --version
  uv run ruff --version
  uv run pyright --version
  uv run pytest --version
  uv run python -c "import gurobipy as gp; print('gurobipy/Gurobi:', gp.gurobi.version())"
fi

exit "$failed"
