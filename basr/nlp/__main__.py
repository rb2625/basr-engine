"""NLP runner: classify + enrich raw docs in Supabase.

Usage:
    python -m basr.nlp                 # classify up to 50 unclassified docs
    python -m basr.nlp --limit 200
    python -m basr.nlp --enrich        # also backfill topics+entities (zero tokens)
    python -m basr.nlp --dry-run       # classify but write nothing

Idempotent by design: docs with an existing classification are skipped, and
``normalized_docs`` has UNIQUE(raw_doc_id). Re-running classifies only what
is new. The lexicon fast path (A7) handles the clear docs with zero tokens;
topics + entities (A8) are always zero-token and are written for every doc
that gets processed, plus any older docs via ``--enrich``.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime, timezone

from .classifier import GroqClassifier, MODEL_VERSION
from .pipeline import classify_docs, enrich_docs
from ..store import SupabaseStore

DEFAULT_LIMIT = 50
FLUSH_EVERY = 10  # persist progress in slices so interruption never loses work


async def run_nlp(*, limit: int = DEFAULT_LIMIT, dry_run: bool = False,
                  enrich: bool = False, enrich_only: bool = False) -> int:
    t0 = time.monotonic()
    print("=" * 60)
    print("  BASR Intelligence Engine - NLP stage")
    print(f"  {datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC   "
          f"dry_run={dry_run} enrich={enrich} enrich_only={enrich_only}")
    print("=" * 60)

    classifier = GroqClassifier()
    # Phase 6 (A17): the local n-gram model is a zero-token fast path between
    # the lexicon and the LLM - it trains in ~1s on the v1 eval items.
    from .local_model import LocalModelClassifier
    local = LocalModelClassifier()
    async with SupabaseStore() as store:
        # Enrichment-only mode: topics + entities backfill, zero tokens, no
        # Groq key needed at all.
        if enrich_only:
            todo = await store.fetch_docs_missing_enrichment(limit)
            print(f"[+] {len(todo)} docs missing topics/entities")
            if todo:
                enriched = await enrich_docs(todo)
                topics_by_doc = {doc_id: topics for doc_id, topics, _ in enriched
                                 if topics}
                entities_by_doc = {doc_id: ents for doc_id, _, ents in enriched
                                   if ents}
                if dry_run:
                    print(f"[dry-run] would enrich {len(todo)} docs "
                          f"(topics={len(topics_by_doc)}, "
                          f"entities={len(entities_by_doc)})")
                    return 0
                tw, ew = await store.upsert_enrichment(
                    topics_by_doc, entities_by_doc,
                    processed_ids=[doc_id for doc_id, _, _ in enriched],
                )
                print(f"[+] enriched {len(todo)} docs "
                      f"(doc_topics={tw}, doc_entities={ew})")
            return 0

        docs = await store.fetch_unclassified_docs(limit)
        print(f"[+] {len(docs)} unclassified docs" + ("" if docs else " - nothing to do"))

        # Classify + enrich + flush in slices so an interrupted backfill keeps
        # what it did (upserts are idempotent - re-running skips classified).
        all_results: list = []
        n_written = c_written = t_written = e_written = 0
        n_lexicon = n_llm = 0
        for start in range(0, len(docs), FLUSH_EVERY):
            slice_docs = docs[start : start + FLUSH_EVERY]
            slice_results = await classify_docs(slice_docs, classifier, local=local)
            all_results.extend(slice_results)
            n_lexicon += sum(1 for r in slice_results if r[3] == "lexicon")
            n_llm += sum(1 for r in slice_results if r[3] == "llm")
            if not dry_run:
                # Classification rows are None on hard model failure - leave
                # those docs unclassified so the next run retries them.
                nw, cw = await store.upsert_nlp_rows(
                    [r[0] for r in slice_results],
                    [r[1] for r in slice_results if r[1] is not None],
                    [(d["id"], lang)
                     for d, (_, _, lang, _, _, _) in zip(slice_docs, slice_results)],
                )
                n_written += nw
                c_written += cw
                topics_by_doc = {r[0]["raw_doc_id"]: r[4] for r in slice_results if r[4]}
                entities_by_doc = {r[0]["raw_doc_id"]: r[5] for r in slice_results if r[5]}
                tw, ew = await store.upsert_enrichment(
                    topics_by_doc, entities_by_doc,
                    processed_ids=[d["id"] for d in slice_docs],
                )
                t_written += tw
                e_written += ew
                print(f"    [flush] {len(all_results)}/{len(docs)} classified")
        results = all_results

        # Backfill pass: topics+entities for older docs (zero tokens).
        if enrich:
            todo = await store.fetch_docs_missing_enrichment(limit)
            print(f"[+] {len(todo)} docs missing topics/entities (backfill)")
            if todo:
                enriched = await enrich_docs(todo)
                topics_by_doc = {doc_id: topics for doc_id, topics, _ in enriched
                                 if topics}
                entities_by_doc = {doc_id: ents for doc_id, _, ents in enriched
                                   if ents}
                if not dry_run:
                    tw, ew = await store.upsert_enrichment(
                        topics_by_doc, entities_by_doc,
                        processed_ids=[doc_id for doc_id, _, _ in enriched],
                    )
                    t_written += tw
                    e_written += ew
                    print(f"    [backfill] {len(todo)} docs enriched "
                          f"(topics={tw}, entities={ew})")
                else:
                    print(f"    [dry-run] would enrich {len(todo)} docs "
                          f"(topics={len(topics_by_doc)}, "
                          f"entities={len(entities_by_doc)})")

        ok = [r for r in results if r[1] is not None
              and (r[1].get("confidence", 0) > 0 or r[1].get("raw"))]
        degraded = len(results) - len(ok)
        langs = {}
        for _, _, lang, _, _, _ in results:
            langs[lang] = langs.get(lang, 0) + 1

        if dry_run:
            print(f"[dry-run] would write {len(results)} normalized + "
                  f"{len(results)} classifications; langs={langs}")
            print(f"[dry-run] routing: {n_lexicon} lexicon (zero tokens) / "
                  f"{n_llm} llm")
            return 0

    elapsed = time.monotonic() - t0
    print("-" * 60)
    print(f"  Classified {len(results)} docs in {elapsed:.1f}s   model={MODEL_VERSION}")
    print(f"  lexicon fast path        : {n_lexicon} (zero tokens)")
    print(f"  llm calls                : {n_llm}")
    print(f"  normalized_docs written : {n_written}")
    print(f"  classifications written : {c_written}")
    print(f"  doc_topics written      : {t_written}")
    print(f"  doc_entities written    : {e_written}")
    print(f"  degraded (low conf)     : {degraded}")
    print(f"  languages               : {', '.join(f'{k}={v}' for k, v in sorted(langs.items()))}")
    print("-" * 60)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="BASR NLP classification stage")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--enrich", action="store_true",
                        help="backfill topics+entities for docs missing them")
    parser.add_argument("--enrich-only", action="store_true",
                        help="only backfill topics+entities (zero tokens, no Groq)")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_nlp(
        limit=args.limit, dry_run=args.dry_run, enrich=args.enrich,
        enrich_only=args.enrich_only)))


if __name__ == "__main__":
    main()
