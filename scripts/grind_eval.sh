#!/usr/bin/env bash
# Tight retry loop for the canonical hybrid v2 eval while the rolling
# token window is nearly exhausted. The window frees ~1.6k tokens every
# ~7 minutes, and each remaining LLM call costs ~1.9k, so a 12-minute
# cadence lets roughly one more call succeed per cycle. Every successful
# classification is banked in the resume cache, so the run converges
# without re-paying prior calls.
#
# Usage:
#   nohup bash scripts/grind_eval.sh > /tmp/basr_grind.log 2>&1 &

cd "$(dirname "$0")/.." || exit 1
PY=./.venv/Scripts/python

echo "=== grind_eval started $(date -u) ==="
attempt=0
while true; do
  attempt=$((attempt + 1))
  echo "--- attempt $attempt at $(date -u) ---"
  PYTHONIOENCODING=utf-8 "$PY" -u -m basr.eval --path hybrid --set v2
  code=$?
  echo "--- attempt $attempt exit=$code at $(date -u) ---"
  if [ "$code" -eq 0 ]; then
    echo "=== DONE: canonical hybrid v2 eval logged at $(date -u) ==="
    exit 0
  fi
  echo "not ready (exit $code), retrying in 12 minutes..."
  sleep 720
done
