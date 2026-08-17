#!/usr/bin/env bash
# Watch Phase 2: retry the canonical hybrid eval until it completes fully.
#
# The gpt-oss-120b free tier's daily token budget is a rolling window that
# frees up gradually as usage ages out (observed empirically - the counter
# dropped ~1.6k in 7 minutes around 20:00 UTC). The eval now refuses to log
# an incomplete run (any failed call -> exit 3, nothing written), so
# retrying is always safe: the scorecard only ever records a fully-measured
# run. This loop retries every 45 minutes until the eval exits 0.
#
# Usage:
#   nohup bash scripts/watch_phase_2.sh > /tmp/basr_phase2_watch.log 2>&1 &

cd "$(dirname "$0")/.." || exit 1
PY=./.venv/Scripts/python

echo "=== watch_phase_2 started $(date -u) ==="
attempt=0
while true; do
  attempt=$((attempt + 1))
  echo "--- attempt $attempt at $(date -u) ---"
  PYTHONIOENCODING=utf-8 "$PY" -u -m basr.eval --path hybrid --set v2
  code=$?
  echo "--- attempt $attempt exit=$code at $(date -u) ---"
  if [ "$code" -eq 0 ]; then
    echo "=== DONE: Phase 2 eval logged at $(date -u) ==="
    exit 0
  fi
  echo "not ready (exit $code), retrying in 45 minutes..."
  sleep 2700
done
