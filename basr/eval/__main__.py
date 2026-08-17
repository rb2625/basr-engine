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

Resume cache (Amendment A18): the free tier's token budget is a rolling
window that frees gradually as usage ages out, so a long LLM-path run can
hit the wall near the end. On an LLM path the harness now persists every
successful (confidence > 0) classification to a local JSON cache keyed by
model version + eval set, so a retry only re-pays for the calls that failed.
The cache is cleared once a run logs a complete scorecard, so it can never
mask a future classifier change.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import tempfile
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from ..nlp.classifier import ClassifyResult, GroqClassifier, MODEL_VERSION
from ..nlp.lexicon import LexiconClassifier, LEXICON_VERSION
from ..nlp.pipeline import HybridClassifier
from ..store import SupabaseStore
from .datasets import DATASETS
from .datasets_v2 import DATASETS_V2
from .harness import compute_metrics, confusion, print_report

CACHE_DIR = os.environ.get("BASR_EVAL_CACHE_DIR", tempfile.gettempdir())
CACHE_FILE = os.path.join(CACHE_DIR, "basr_eval_cache.json")


class ResultCache:
    """Disk cache of successful eval classifications, keyed by
    model version + eval set so different classifiers never mix."""

    def __init__(self, key: str, path: str = CACHE_FILE) -> None:
        self.key = key
        self.path = path
        self._data: dict[str, dict] = {}
        try:
            with open(path, encoding="utf-8") as f:
                blob = json.load(f)
            self._data = blob.get(key, {})
        except (OSError, ValueError):
            self._data = {}

    def get(self, text: str) -> ClassifyResult | None:
        entry = self._data.get(text)
        if not entry:
            return None
        try:
            return ClassifyResult(**{k: v for k, v in entry.items() if k in
                                     ClassifyResult.__dataclass_fields__})
        except (TypeError, ValueError):
            return None

    def put(self, text: str, result: ClassifyResult) -> None:
        if result.confidence <= 0.0:
            return  # failed calls are never cached - they must be retried
        self._data[text] = asdict(result)
        self._save()

    def _save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({self.key: self._data}, f)
        except OSError:
            pass  # cache is an optimization; a full re-run is still correct

    def clear(self) -> None:
        try:
            os.remove(self.path)
        except OSError:
            pass

    def __len__(self) -> int:
        return len(self._data)

_TASK_EXTRACT = {
    "sentiment": lambda r: r.sentiment_label,
    "signal": lambda r: r.signal_type,
}

HYBRID_VERSION = f"hybrid-local-v1+{MODEL_VERSION}"  # A18: local-first routing


def _make_classifier(path: str):
    if path == "lexicon":
        return LexiconClassifier(), LEXICON_VERSION
    if path == "hybrid":
        return HybridClassifier(), HYBRID_VERSION
    return GroqClassifier(), MODEL_VERSION


def _score_task(classifier, items, task: str, *, results: dict | None = None,
                cache: ResultCache | None = None) -> dict:
    """Classify (or reuse) each item and score one task's labels."""
    y_true: list[str] = []
    y_pred: list[str] = []
    failures = 0
    extract = _TASK_EXTRACT[task]
    for i, item in enumerate(items, 1):
        text = item["text"]
        result = results.get(text) if results is not None else None
        if result is None and cache is not None:
            result = cache.get(text)
        if result is None:
            result = classifier.classify(text)
            if results is not None:
                results[text] = result
            if cache is not None:
                cache.put(text, result)
        expected = item["label"]
        predicted = extract(result)
        y_true.append(expected)
        y_pred.append(predicted)
        if predicted != expected:
            print(f"    [{i}/{len(items)}] MISMATCH expected={expected!r} "
                  f"got={predicted!r} | {text[:70]}")
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
                       dry_run: bool = False, path: str = "llm",
                       eval_set: str = "v2") -> int:
    t0 = time.monotonic()
    datasets = DATASETS_V2 if eval_set == "v2" else DATASETS
    print("=" * 60)
    print("  BASR eval harness - classifier scorecard")
    print(f"  {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC   "
          f"dry_run={dry_run} path={path} set={eval_set}")
    print("=" * 60)

    classifier, model_version = _make_classifier(path)
    store = None if dry_run else SupabaseStore()
    if store is not None:
        await store.open()

    cache: ResultCache | None = None
    if path in ("llm", "hybrid") and not dry_run:
        cache = ResultCache(f"{model_version}|{eval_set}")
        if len(cache):
            print(f"[+] resume cache: {len(cache)} prior successful "
                  f"classifications loaded (retry only re-pays failed calls)")

    try:
        datasets = [ds for ds in datasets if not task or ds["task"] == task]
        all_metrics: list[tuple[str, dict]] = []

        if len(datasets) > 1 and path != "lexicon":
            # Combined mode: classify each unique text ONCE (production
            # behavior) and score every task from the same result.
            results: dict[str, object] = {}
            for ds in datasets:
                items = _items(ds, limit)
                print(f"\n[+] Task {ds['task']!r} - dataset {ds['name']} "
                      f"({len(items)} items, shared single-pass calls)")
                metrics = _score_task(classifier, items, ds["task"],
                                      results=results, cache=cache)
                print_report(f"  {ds['name']} ({ds['task']})", metrics)
                all_metrics.append((ds["name"], metrics))
        else:
            for ds in datasets:
                items = _items(ds, limit)
                print(f"\n[+] Task {ds['task']!r} - dataset {ds['name']} ({len(items)} items)")
                metrics = _score_task(classifier, items, ds["task"], cache=cache)
                print_report(f"  {ds['name']} ({ds['task']})", metrics)
                all_metrics.append((ds["name"], metrics))

        if dry_run or store is None:
            return 0

        # Persist datasets (idempotent) + this run's scores. A run with ANY
        # failed calls (confidence 0 - usually the daily budget wall) is
        # INCOMPLETE and must never be published as a scorecard: log nothing
        # so a retry later produces the one true measurement.
        for ds in datasets:
            await store.upsert_eval_dataset(ds["name"], ds["lang"], ds["task"], ds["items"])
        incomplete = any(m["failures"] > 0 for _, m in all_metrics)
        if incomplete:
            print("\n[!] eval incomplete (failed calls) - NOT logged to eval_runs.")
            print("    Retry when the daily token budget has headroom; the scorecard")
            print("    only ever records a fully-measured run.")
            return 3
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
        if cache is not None:
            cache.clear()
            print("[+] resume cache cleared - the scorecard now reflects this run only")
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
    parser.add_argument("--agents", action="store_true",
                        help="score the Phase 5 agents (severity + brief)")
    parser.add_argument("--path", choices=("llm", "lexicon", "hybrid"),
                        default="llm", help="classifier to score")
    parser.add_argument("--set", choices=("v1", "v2"), default="v2",
                        help="eval set: v2 is the fresh Gate-2 set (default)")
    args = parser.parse_args()
    if args.agents:
        from .agents import run_agents_eval
        raise SystemExit(asyncio.run(run_agents_eval(dry_run=args.dry_run)))
    raise SystemExit(asyncio.run(run_eval_cli(
        limit=args.limit, task=args.task, dry_run=args.dry_run,
        path=args.path, eval_set=args.set)))


if __name__ == "__main__":
    main()
