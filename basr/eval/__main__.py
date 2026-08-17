"""Run the eval harness over the labeled datasets.

Usage:
    python -m basr.eval                 # score both tasks (LLM), log to Supabase
    python -m basr.eval --path lexicon  # score the zero-token fast path only
    python -m basr.eval --path hybrid   # production routing (lexicon + LLM)
    python -m basr.eval --limit 12      # quick slice
    python -m basr.eval --task sentiment
    python -m basr.eval --dry-run       # score only, no DB writes

Budget design (Amendment A10): when BOTH tasks run on an LLM path, each item
is classified ONCE (one LLM call returning all fields, exactly like the
production pipeline) and both task labels are scored from that result. This
halves the token cost versus the old two-pass design and keeps the measured
scorecard aligned with how the pipeline actually classifies docs.

Note: each LLM-path item costs one Groq call (paced ~6s on the free tier), so
a full run of both tasks over 500 items takes ~40 minutes and ~150-190k
tokens - under the gpt-oss-120b free-tier daily cap of 200k. ``--limit``
slices the items for quick verification runs. The lexicon path is instant
and free.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime, timezone

from ..nlp.classifier import GroqClassifier, MODEL_VERSION
from ..nlp.lexicon import LexiconClassifier, LEXICON_VERSION
from ..nlp.pipeline import HybridClassifier
from ..store import SupabaseStore
from .datasets import DATASETS
from .harness import compute_metrics, confusion, print_report

_TASK_EXTRACT = {
    "sentiment": lambda r: r.sentiment_label,
    "signal": lambda r: r.signal_type,
}

HYBRID_VERSION = f"hybrid-lexicon-v1+{MODEL_VERSION}"


def _make_classifier(path: str):
    if path == "lexicon":
        return LexiconClassifier(), LEXICON_VERSION
    if path == "hybrid":
        return HybridClassifier(), HYBRID_VERSION
    return GroqClassifier(), MODEL_VERSION


def _score_task(classifier, items, task: str, *, results: dict | None = None) -> dict:
    """Classify (or reuse) each item and score one task's labels."""
    y_true: list[str] = []
    y_pred: list[str] = []
    failures = 0
    extract = _TASK_EXTRACT[task]
    for i, item in enumerate(items, 1):
        result = results.get(item["text"]) if results is not None else None
        if result is None:
            result = classifier.classify(item["text"])
            if results is not None:
                results[item["text"]] = result
        expected = item["label"]
        predicted = extract(result)
        y_true.append(expected)
        y_pred.append(predicted)
        if predicted != expected:
            print(f"    [{i}/{len(items)}] MISMATCH expected={expected!r} "
                  f"got={predicted!r} | {item['text'][:70]}")
        if result.confidence == 0.0:
            failures += 1
    metrics = compute_metrics(y_true, y_pred)
    metrics["task"] = task
    metrics["confusion"] = confusion(y_true, y_pred)
    metrics["failures"] = failures
    return metrics


def _items(ds: dict, limit: int | None) -> list[dict]:
    items = ds["items"]
    if limit:
        # Balanced slice: take every nth item so the quick run still
        # covers ar / arz / en / sarcasm.
        step = max(1, len(items) // limit)
        items = items[::step][:limit]
    return items


async def run_eval_cli(*, limit: int | None = None, task: str | None = None,
                       dry_run: bool = False, path: str = "llm") -> int:
    t0 = time.monotonic()
    print("=" * 60)
    print("  BASR eval harness - classifier scorecard")
    print(f"  {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC   "
          f"dry_run={dry_run} path={path}")
    print("=" * 60)

    classifier, model_version = _make_classifier(path)
    store = None if dry_run else SupabaseStore()
    if store is not None:
        await store.open()

    try:
        datasets = [ds for ds in DATASETS if not task or ds["task"] == task]
        all_metrics: list[tuple[str, dict]] = []

        if len(datasets) > 1 and path != "lexicon":
            # Combined mode: classify each unique text ONCE (production
            # behavior) and score every task from the same result.
            results: dict[str, object] = {}
            for ds in datasets:
                items = _items(ds, limit)
                print(f"\n[+] Task {ds['task']!r} - dataset {ds['name']} "
                      f"({len(items)} items, shared single-pass calls)")
                metrics = _score_task(classifier, items, ds["task"], results=results)
                print_report(f"  {ds['name']} ({ds['task']})", metrics)
                all_metrics.append((ds["name"], metrics))
        else:
            for ds in datasets:
                items = _items(ds, limit)
                print(f"\n[+] Task {ds['task']!r} - dataset {ds['name']} ({len(items)} items)")
                metrics = _score_task(classifier, items, ds["task"])
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
                model_version=model_version,
                accuracy=metrics["accuracy"],
                precision=metrics["macro_precision"],
                recall=metrics["macro_recall"],
                f1=metrics["macro_f1"],
                detail={"per_class": metrics["per_class"], "n": metrics["n"],
                        "confusion": metrics["confusion"]},
            )
            print(f"[+] eval_runs logged for {name} ({model_version}): {ok}")
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
    parser.add_argument("--path", choices=("llm", "lexicon", "hybrid"),
                        default="llm", help="classifier to score")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_eval_cli(
        limit=args.limit, task=args.task, dry_run=args.dry_run, path=args.path)))


if __name__ == "__main__":
    main()
