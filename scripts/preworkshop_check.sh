#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "== 1. Development environment =="
./scripts/verify_environment.sh

echo
echo "== 2. NVIDIA/OpenCode configuration =="
./scripts/verify_nvidia_config.sh

echo
echo "== 3. Gurobi smoke test =="
uv run python scripts/gurobi_smoke_test.py

echo
echo "== 4. Full Gurobi license test =="
uv run python scripts/gurobi_full_license_check.py

echo
echo "Pre-workshop automated checks passed."
echo
echo "Final manual check:"
echo "  Run 'opencode' from this repository and ask:"
echo "  'Read AGENTS.md and briefly tell me which verification commands this project requires.'"
