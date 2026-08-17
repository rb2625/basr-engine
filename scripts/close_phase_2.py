"""Close Phase 2 in one command after the daily token budget resets.

The gpt-oss-120b free tier caps at 200,000 tokens/day (Amendment A5/A10).
The canonical hybrid eval needs ~154k tokens, so it can only run after the
00:00 UTC reset. This script:

1. probes the budget with one tiny call (the counter rides the 429 error),
2. runs the canonical eval when budget is available (~40 min, logs to
   eval_runs),
3. reads the logged hybrid scores and reports the Phase 2 DoD verdict
   (sentiment macro-F1 >= 0.88).

Usage (from the repo root):
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python scripts/close_phase_2.py
"""

from __future__ import annotations

import asyncio
import os
import sys

# Make the repo root importable when run as scripts/close_phase_2.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from basr.eval.__main__ import run_eval_cli
from basr.store.store import SupabaseStore


def probe_budget() -> bool:
    """One tiny call. Returns True when the model answers (budget available)."""
    from groq import Groq
    from basr.config import get_settings
    client = Groq(api_key=get_settings().groq_api_key)
    try:
        client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Reply with just: OK"}],
            max_tokens=8,
        )
        return True
    except Exception as exc:
        print(f"[-] budget probe failed: {str(exc)[:200]}")
        return False


async def latest_hybrid_scores() -> list[dict]:
    async with SupabaseStore() as store:
        ds = await store._with_retry(
            lambda: store._client.table("eval_datasets")
            .select("id,name,task").execute()
        )
        name_by_id = {d["id"]: d for d in (ds.data or [])}
        resp = await store._with_retry(
            lambda: store._client.table("eval_runs")
            .select("dataset_id,model_version,accuracy,recall,f1,detail,created_at")
            .like("model_version", "hybrid-%")
            .order("created_at", desc=True)
            .limit(4)
            .execute()
        )
        for r in (resp.data or []):
            info = name_by_id.get(r.get("dataset_id")) or {}
            r["dataset_name"] = info.get("name", f"ds={r.get('dataset_id')}")
            r["task"] = info.get("task", "")
        return resp.data or []


async def main() -> int:
    print("=" * 60)
    print("  Close Phase 2: canonical hybrid eval + DoD verdict")
    print("=" * 60)

    if not probe_budget():
        print("\n[!] Budget still exhausted - the daily counter resets at 00:00")
        print("    UTC (~4h). Re-run this script after the reset. Nothing was")
        print("    logged.")
        return 1

    print("\n[+] Budget available. Running the canonical eval (~40 min)...")
    # Run in-process (a nested subprocess breaks on Windows - WinError 10106
    # on asyncio's _overlapped import) and it shares the probe's client anyway.
    code = await run_eval_cli(path="hybrid", eval_set="v2")
    if code != 0:
        print("[-] eval did not complete cleanly (incomplete runs are never")
        print("    logged - retry when the budget has more headroom)")
        return 1

    rows = await latest_hybrid_scores()
    if not rows:
        print("[-] no hybrid eval_runs found after the run")
        return 1

    print("\nPhase 2 DoD check (sentiment macro-F1 >= 0.88 on eval v2):")
    verdict = True
    for r in rows:
        name = r.get("dataset_name", "")
        task = r.get("task", "")
        f1 = float(r.get("f1") or 0.0)
        acc = float(r.get("accuracy") or 0.0)
        passed = task == "sentiment" and f1 >= 0.88
        if task == "sentiment":
            verdict = passed
        print(f"  {name:16s} acc={acc:.4f} macro-F1={f1:.4f} "
              f"{'PASS' if passed else ('' if task != 'sentiment' else 'BELOW BAR')}")
        print(f"    {str(r.get('created_at'))[:16]}  {r.get('model_version')}")

    if verdict:
        print("\n[+] PHASE 2 DoD PASSED - sentiment F1 >= 88%. Next: drain the")
        print("    classification backlog inside the same daily cap")
        print("    (python -m basr.orchestrator --nlp --nlp-limit 40).")
    else:
        print("\n[-] Phase 2 stays open: sentiment F1 below 88%. The plan's")
        print("    unlock is the fine-tuned Gulf-Arabic model (Phase 6); the")
        print("    hybrid prompt/lexicon can be tuned further meanwhile.")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
