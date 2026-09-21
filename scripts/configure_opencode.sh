#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_config="$repo_root/opencode-setup/opencode.json"
target_dir="$HOME/.config/opencode"
target_config="$target_dir/opencode.json"

if [[ ! -f "$source_config" ]]; then
  echo "ERROR: Missing $source_config" >&2
  exit 1
fi

mkdir -p "$target_dir"
chmod 700 "$target_dir"

printf "Paste your NVIDIA API key (input hidden): "
IFS= read -r -s api_key
printf "\n"

if [[ -z "$api_key" || "$api_key" != nvapi-* ]]; then
  echo "ERROR: Expected an NVIDIA API key beginning with 'nvapi-'." >&2
  exit 1
fi

umask 077
tmp="$(mktemp "$target_dir/opencode.json.XXXXXX")"
trap 'rm -f "$tmp"' EXIT

# The NVIDIA API key alphabet does not normally contain the chosen delimiter.
# Escape '&' because it has a special meaning in sed replacements.
escaped_key="${api_key//&/\\&}"
sed "s|nvapi-PASTE-YOUR-KEY-HERE|$escaped_key|g" "$source_config" > "$tmp"

mv "$tmp" "$target_config"
chmod 600 "$target_config"
trap - EXIT

echo "OpenCode configuration written to:"
echo "  $target_config"
echo
echo "Configured model:"
echo "  nvidia/nemotron-3-ultra-550b-a55b"
echo "Configured endpoint:"
echo "  https://integrate.api.nvidia.com/v1"
echo
echo "The API key was written only to the global OpenCode configuration."
