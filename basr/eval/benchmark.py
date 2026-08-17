"""Benchmark candidate Groq models on a sample of the BASR eval set.

Used for Amendment A10: when Groq retired llama-3.3-70b-versatile, this script
measured the remaining free-tier models (gpt-oss-120b won) through the exact
same harness used for published scorecards - measured, not vibes.

Usage:
    python -m basr.eval.benchmark [--items 18] [--gap 4] [--task signal]
"""

from __future__ import annotations

import argparse
import time

from ..nlp import classifier as clf_mod
from ..nlp.classifier import GroqClassifier
from .datasets import ITEMS
from .harness import print_report, run_eval

CANDIDATES = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

EXTRACT = {
    "signal": lambda r: r.signal_type,
    "sentiment": lambda r: r.sentiment_label,
}


def sample_items(n: int, task: str) -> list[dict]:
    """Balanced sample across ar/arz/en, forcing in sarcasm + trap items."""
    by_lang: dict[str, list] = {"ar": [], "arz": [], "en": []}
    for it in ITEMS:
        by_lang.setdefault(it.lang, []).append(it)
    picked: list = []
    per = max(1, n // 3)
    for lang in ("ar", "arz", "en"):
        items = by_lang[lang]
        step = max(1, len(items) // per)
        picked.extend(items[::step][:per])
    extra = [it for it in ITEMS
             if "sarcasm" in it.note or "personal" in it.note or "question" in it.note]
    for it in extra:
        if len(picked) >= n:
            break
        if it not in picked:
            picked.append(it)
    return [{"text": it.text, "label": getattr(it, task)} for it in picked[:n]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=int, default=18)
    ap.add_argument("--gap", type=float, default=4.0)
    ap.add_argument("--task", choices=tuple(EXTRACT), default="signal")
    args = ap.parse_args()

    items = sample_items(args.items, args.task)
    print(f"[bench] {len(items)} items, task={args.task}, gap={args.gap}s")

    for model in CANDIDATES:
        clf_mod.MODEL = model
        clf_mod.MODEL_VERSION = f"bench-{model}"
        c = GroqClassifier(min_gap_s=args.gap, max_attempts=2)
        t0 = time.monotonic()
        try:
            metrics = run_eval(c, items, args.task, extract=EXTRACT[args.task])
            print_report(f"{model} ({args.task})", metrics)
        except Exception as e:  # noqa: BLE001
            print(f"[bench] {model} FAILED: {str(e)[:200]}")
        print(f"[bench] {model} took {time.monotonic() - t0:.1f}s")


if __name__ == "__main__":
    main()
