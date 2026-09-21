#!/usr/bin/env bash
set -euo pipefail

config="$HOME/.config/opencode/opencode.json"

if [[ ! -s "$config" ]]; then
  echo "ERROR: $config is missing or empty." >&2
  exit 1
fi

model="$(jq -r '.model // empty' "$config")"
endpoint="$(jq -r '.provider.nvidia.options.baseURL // empty' "$config")"
api_key="$(jq -r '.provider.nvidia.options.apiKey // empty' "$config")"

expected_model="nvidia/nemotron-3-ultra-550b-a55b"
expected_endpoint="https://integrate.api.nvidia.com/v1"

failed=0

if [[ "$model" == "$expected_model" ]]; then
  echo "NVIDIA model:    OK"
else
  echo "NVIDIA model:    WRONG ($model)" >&2
  failed=1
fi

if [[ "$endpoint" == "$expected_endpoint" ]]; then
  echo "NVIDIA endpoint: OK"
else
  echo "NVIDIA endpoint: WRONG ($endpoint)" >&2
  failed=1
fi

if [[ "$api_key" == nvapi-* && "$api_key" != "nvapi-PASTE-YOUR-KEY-HERE" ]]; then
  echo "NVIDIA API key:  configured"
else
  echo "NVIDIA API key:  missing or still placeholder" >&2
  failed=1
fi

exit "$failed"
