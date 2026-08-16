"""NLP runner: classify every unclassified raw doc in Supabase.

Usage:
    python -m basr.nlp                 # classify up to 50 unclassified docs
    python -m basr.nlp --limit 200
    python -m basr.nlp --dry-run       # classify but write nothing

Idempotent by design: docs with an existing classification are skipped, and
``normalized_docs`` has UNIQUE(raw_doc_id). Re-running classifies only what
is new. Pacing (8s between Groq calls on the free tier) means ~100 docs take
~15 minutes - run it as the second stage of the cron.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime, timezone

from .classifier import GroqClassifier, MODEL_VERSION
from .pipeline import classify_docs
from ..store import SupabaseStore

DEFAULT_LIMIT = 50
FLUSH_EVERY = 10  # persist progress in slices so interruption never loses work


async def run_nlp(*, limit: int = DEFAULT_LIMIT, dry_run: bool = False) -> int:
    t0 = time.monotonic()
    print("=" * 60)
    print("  BASR Intelligence Engine - NLP classification stage")
    print(f"  {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC   dry_run={dry_run}")
    print("=" * 60)

    classifier = GroqClassifier()
    async with SupabaseStore() as store:
        docs = await store.fetch_unclassified_docs(limit)
        print(f"[+] {len(docs)} unclassified docs" + ("" if docs else " - nothing to do"))
        if not docs:
            return 0

        # Classify + flush in slices so an interrupted backfill keeps what it
        # did (upserts are idempotent - re-running skips classified docs).
        all_results: list = []
        n_written = c_written = 0
        for start in range(0, len(docs), FLUSH_EVERY):
            slice_docs = docs[start : start + FLUSH_EVERY]
            slice_results = await classify_docs(slice_docs, classifier)
            all_results.extend(slice_results)
            if not dry_run:
                # Classification rows are None on hard model failure - leave
                # those docs unclassified so the next run retries them.
                nw, cw = await store.upsert_nlp_rows(
                    [r[0] for r in slice_results],
                    [r[1] for r in slice_results if r[1] is not None],
                    [(d["id"], lang)
                     for d, (_, _, lang) in zip(slice_docs, slice_results)],
                )
                n_written += nw
                c_written += cw
                print(f"    [flush] {len(all_results)}/{len(docs)} classified")
        results = all_results

        ok = [r for r in results if r[1] is not None
              and (r[1].get("confidence", 0) > 0 or r[1].get("raw"))]
        degraded = len(results) - len(ok)
        langs = {}
        for _, _, lang in results:
            langs[lang] = langs.get(lang, 0) + 1

        if dry_run:
            print(f"[dry-run] would write {len(results)} normalized + "
                  f"{len(results)} classifications; langs={langs}")
            return 0

    elapsed = time.monotonic() - t0
    print("-" * 60)
    print(f"  Classified {len(results)} docs in {elapsed:.1f}s   model={MODEL_VERSION}")
    print(f"  normalized_docs written : {n_written}")
    print(f"  classifications written : {c_written}")
    print(f"  degraded (low conf)     : {degraded}")
    print(f"  languages               : {', '.join(f'{k}={v}' for k, v in sorted(langs.items()))}")
    print("-" * 60)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="BASR NLP classification stage")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_nlp(limit=args.limit, dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
