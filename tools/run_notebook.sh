#!/usr/bin/env bash
# Runs a notebook top to bottom, headless, in a fresh kernel. Fails on any cell error.
# The organiser asks that the Colab notebook "run top to bottom without errors".
# Usage: tools/run_notebook.sh notebook.ipynb [timeout-seconds] [executed-copy-path]
set -euo pipefail
cd "$(dirname "$0")/.."
nb=$1; limit=${2:-1800}
out=${3:-$(mktemp -d)/executed.ipynb}
.venv/bin/jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout="$limit" \
  --ExecutePreprocessor.kernel_name=python3 --output "$out" "$nb" >/dev/null 2>"$out.log" || {
  tail -30 "$out.log"; echo "run_notebook: FAILED $nb"; exit 1; }
echo "run_notebook: $nb ran top to bottom ($out)"
