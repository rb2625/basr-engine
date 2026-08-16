"""Run the eval harness over the labeled datasets.

Usage:
    python -m basr.eval                 # score both tasks, log to Supabase
    python -m basr.eval --limit 12      # quick slice (fewer Groq calls)
    python -m basr.eval --task sentiment
    python -m basr.eval --dry-run       # score only, no DB writes

Note: each scored item costs one Groq call (paced ~8s on the free tier), so a
full run of both tasks over 80 items takes ~20 minutes. ``--limit`` slices the
items for quick verification runs.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime, timezone

from ..nlp.classifier import GroqClassifier, MODEL_VERSION
from ..store import SupabaseStore
from .datasets import DATASETS
from .harness import print_report, run_eval

_TASK_EXTRACT = {
    "sentiment": lambda r: r.sentiment_label,
    "signal": lambda r: r.signal_type,
}


async def run_eval_cli(*, limit: int | None = None, task: str | None = None,
                       dry_run: bool = False) -> int:
    t0 = time.monotonic()
    print("=" * 60)
    print("  BASR eval harness — classifier scorecard")
    print(f"  {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC   dry_run={dry_run}")
    print("=" * 60)

    classifier = GroqClassifier()
    all_metrics: list[tuple[str, dict]] = []
    store = None if dry_run else SupabaseStore()
    if store is not None:
        await store.open()

    try:
        for ds in DATASETS:
            if task and ds["task"] != task:
                continue
            items = ds["items"]
            if limit:
                # Balanced slice: take every nth item so the quick run still
                # covers ar / arz / en / sarcasm.
                step = max(1, len(items) // limit)
                items = items[::step][:limit]
            print(f"\n[+] Task {ds['task']!r} — dataset {ds['name']} ({len(items)} items)")
            metrics = run_eval(
                classifier, items, ds["task"],
                extract=_TASK_EXTRACT[ds["task"]],
            )
            print_report(f"  {ds['name']} ({ds['task']})", metrics)
            all_metrics.append((ds["name"], metrics))

        if dry_run or store is None:
            return 0

        # Persist datasets (idempotent) + this run's scores.
        for ds in DATASETS:
            await store.upsert_eval_dataset(ds["name"], ds["lang"], ds["task"], ds["items"])
        for name, metrics in all_metrics:
            ok = await store.log_eval_run(
                dataset_name=name,
                model_version=MODEL_VERSION,
                accuracy=metrics["accuracy"],
                precision=metrics["macro_precision"],
                recall=metrics["macro_recall"],
                f1=metrics["macro_f1"],
                detail={"per_class": metrics["per_class"], "n": metrics["n"],
                        "confusion": metrics["confusion"]},
            )
            print(f"[+] eval_runs logged for {name}: {ok}")
    finally:
        if store is not None:
            await store.close()

    print(f"\n[+] Eval finished in {time.monotonic() - t0:.1f}s")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="BASR eval harness")
    parser.add_argument("--limit", type=int, default=None, help="max items per task")
    parser.add_argument("--task", choices=("sentiment", "signal"), default=None)
    parser.add_argument("--dry-run", action="store_true", help="score only, no DB writes")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_eval_cli(
        limit=args.limit, task=args.task, dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
