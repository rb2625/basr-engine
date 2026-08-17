"""End-to-end ingestion pipeline: all sources -> Supabase store.

This is the single entry point the cron runs. It:

1. Builds every configured source adapter.
2. Runs them concurrently, staggered by a small offset (politeness), each with
   its own timeout - one failing source never kills the run (working rule 3).
3. Dedupes across sources, then upserts into ``raw_docs`` (idempotent).
4. Logs the run to ``pipeline_runs`` (graceful if the table is missing).
5. Prints a structured summary and sets the exit code (0 = store succeeded).

Usage:
    python -m basr.orchestrator            # full run
    python -m basr.orchestrator --dry-run  # fetch only, no DB writes
    python -m basr.orchestrator --limit 50 # cap docs per source
    python -m basr.orchestrator --nlp      # run the NLP classification stage after ingestion
    python -m basr.orchestrator --intel    # run the Phase 4 early-warning stage
"""

from __future__ import annotations

import argparse
import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .adapters.apple_reviews import AppleReviewsAdapter
from .adapters.bluesky_firehose import BlueskyFirehoseAdapter
from .adapters.news_rss import NewsRSSAdapter
from .adapters.reddit_arctic import ArcticShiftRedditAdapter
from .adapters.youtube_comments import QuotaExhausted, YouTubeCommentsAdapter
from .config import (
    DEFAULT_FETCH_LIMIT,
    DEFAULT_SINCE_HOURS,
    REDDIT_SUBREDDITS,
    get_settings,
)
from .store import SupabaseStore

# NLP stage (Phase 2) - imported lazily inside run_pipeline so a missing
# groq key never breaks plain ingestion.
_NLP_DEFAULT_LIMIT = 50

# Per-source runtime knobs (bounded so a cron run finishes in minutes).
SOURCE_TIMEOUT_S = 300          # hard ceiling per source
FIREHOSE_WINDOW_S = 45          # Bluesky listen window
REDDIT_MAX_PAGES = 2            # archive pagination depth per (sub, kind)
REDDIT_REQUEST_GAP_S = 0.8      # politeness gap between archive calls
YOUTUBE_VIDEOS_PER_CHANNEL = 3
YOUTUBE_COMMENTS_PER_VIDEO = 50

# Small stagger so sources don't all hit their hosts at the same instant.
_STAGGER_S = {
    "reddit_arctic": 0.0,
    "news_rss": 0.5,
    "apple_reviews": 1.0,
    "youtube_comments": 1.5,
    "bluesky_firehose": 2.0,
}


@dataclass
class SourceResult:
    name: str
    docs: list = field(default_factory=list)
    error: str | None = None


def _build_adapters(limit: int) -> list[tuple[str, object, dict]]:
    """Return (name, adapter, fetch_kwargs) for every configured source."""
    since = datetime.now(timezone.utc) - timedelta(hours=DEFAULT_SINCE_HOURS)
    sources: list[tuple[str, object, dict]] = [
        (
            "reddit_arctic",
            ArcticShiftRedditAdapter(
                subreddits=REDDIT_SUBREDDITS,
                max_pages=REDDIT_MAX_PAGES,
                request_gap_s=REDDIT_REQUEST_GAP_S,
            ),
            {"since": since, "limit": limit},
        ),
        ("news_rss", NewsRSSAdapter(), {"since": since, "limit": limit}),
        ("apple_reviews", AppleReviewsAdapter(), {"since": since, "limit": limit}),
        (
            "youtube_comments",
            YouTubeCommentsAdapter(
                videos_per_channel=YOUTUBE_VIDEOS_PER_CHANNEL,
                comments_per_video=YOUTUBE_COMMENTS_PER_VIDEO,
            ),
            {"since": since, "limit": limit},
        ),
        (
            "bluesky_firehose",
            BlueskyFirehoseAdapter(),
            {"since": since, "limit": limit, "duration_s": FIREHOSE_WINDOW_S},
        ),
    ]
    return sources


async def _run_one(name: str, adapter: object, kwargs: dict, timeout: float, offset: float) -> SourceResult:
    """Run one source with a stagger offset, per-source timeout, and isolation."""
    if offset > 0:
        await asyncio.sleep(offset)
    try:
        docs = await asyncio.wait_for(adapter.fetch(**kwargs), timeout=timeout)
        return SourceResult(name=name, docs=docs)
    except QuotaExhausted as exc:
        print(f"[-] {name}: YouTube daily quota exhausted - skipping source this run")
        return SourceResult(name=name, error=f"quota_exhausted: {exc}")
    except asyncio.TimeoutError:
        print(f"[-] {name}: timed out after {timeout}s - continuing with other sources")
        return SourceResult(name=name, error=f"timeout after {timeout}s")
    except Exception as exc:  # source isolation: never let one source kill the run
        print(f"[-] {name}: {exc.__class__.__name__}: {str(exc)[:120]}")
        return SourceResult(name=name, error=f"{exc.__class__.__name__}: {str(exc)[:120]}")


async def run_pipeline(*, limit: int | None = None, dry_run: bool = False,
                       nlp: bool = False, nlp_limit: int | None = None,
                       intel: bool = False, agents: bool = False) -> int:
    """Run the full ingestion pipeline. Returns the process exit code."""
    t0 = time.monotonic()
    started_at = datetime.now(timezone.utc)
    limit = limit or DEFAULT_FETCH_LIMIT

    print("=" * 60)
    print("  BASR Intelligence Engine - ingestion pipeline")
    print(f"  {started_at:%Y-%m-%d %H:%M:%S} UTC   dry_run={dry_run}")
    print("=" * 60)

    # --- 1. Fetch from all sources -------------------------------------------------
    sources = _build_adapters(limit)
    results: list[SourceResult] = []
    for name, adapter, kwargs in sources:
        offset = _STAGGER_S.get(name, 0.0)
        result = await _run_one(name, adapter, kwargs, SOURCE_TIMEOUT_S, offset)
        results.append(result)
        print(f"    [{'OK' if result.error is None else 'FAIL'}] {name}: {len(result.docs)} docs"
              + (f"  ({result.error})" if result.error else ""))

    # --- 2. Merge + cross-source dedupe ----------------------------------------------
    merged: dict[str, object] = {}
    for res in results:
        for doc in res.docs:
            merged[doc.dedupe_key()] = doc
    docs = list(merged.values())
    source_counts = {res.name: len(res.docs) for res in results}
    failures = [f"{res.name}: {res.error}" for res in results if res.error]

    print(f"\n[+] Fetched {len(docs)} unique docs across "
          f"{sum(source_counts.values())} raw items from {len(results)} sources")

    # --- 3. Persist -------------------------------------------------------------------
    inserted = skipped = 0
    store_error: str | None = None
    if dry_run:
        print("[dry-run] skipping DB write")
        status = "dry_run"
    else:
        try:
            async with SupabaseStore() as store:
                counts = await store.upsert_raw_docs(docs)
                inserted, skipped = counts.inserted, counts.skipped
                print(f"[+] Store: {inserted} inserted, {skipped} duplicates skipped "
                      f"({counts.batches} batches)")
                await store.log_run(
                    status="success" if not failures else "partial",
                    source_counts=source_counts,
                    inserted=inserted,
                    skipped=skipped,
                    failures=failures,
                    started_at=started_at,
                    finished_at=datetime.now(timezone.utc),
                )
            status = "success" if not failures else "partial"
        except Exception as exc:
            store_error = f"{exc.__class__.__name__}: {str(exc)[:160]}"
            print(f"[-] Store failed: {store_error}")
            status = "failed"

    # --- 4. NLP classification stage (Phase 2) -------------------------------
    if nlp and not store_error:
        from .nlp.__main__ import run_nlp  # lazy: needs GROQ_API_KEY
        try:
            await run_nlp(limit=nlp_limit or _NLP_DEFAULT_LIMIT, dry_run=dry_run,
                          enrich=True)
        except Exception as exc:
            print(f"[-] NLP stage failed: {exc.__class__.__name__}: {str(exc)[:120]}")

    # --- 4b. Early-warning stage (Phase 4) -----------------------------------
    if intel and not store_error:
        from .intel.__main__ import run_intel  # lazy import, zero LLM cost
        try:
            await run_intel(aggregate=True, detect=True, deliver=True,
                            dry_run=dry_run)
        except Exception as exc:
            print(f"[-] Intel stage failed: {exc.__class__.__name__}: {str(exc)[:120]}")

    # --- 4c. Agents stage (Phase 5): scheduled reports ------------------------
    if agents and not store_error:
        from .agents.reports import build_report, deliver_reports
        try:
            # Daily report every run; weekly only when none exists for the
            # current week yet (the cron runs twice a day, so this is the
            # idempotence guard).
            await build_report(store, "daily", dry_run=dry_run)
            weekly_done = False
            if not dry_run:
                from datetime import timedelta
                today = datetime.now(timezone.utc).date()
                week_ago = (today - timedelta(days=7)).isoformat()
                resp = await store._with_retry(
                    lambda: store._client.table("reports")
                    .select("id").eq("kind", "weekly")
                    .gte("period_end", week_ago).limit(1).execute())
                weekly_done = bool((resp.data or []))
            if not weekly_done:
                await build_report(store, "weekly", dry_run=dry_run)
            await deliver_reports(store)
        except Exception as exc:
            print(f"[-] Agents stage failed: {exc.__class__.__name__}: {str(exc)[:120]}")

    # --- 5. Summary ---------------------------------------------------------------------
    elapsed = time.monotonic() - t0
    finished_at = datetime.now(timezone.utc)
    lines = [
        "-" * 60,
        f"  Run finished in {elapsed:.1f}s   status={status}",
        f"  sources : {', '.join(f'{n}={c}' for n, c in sorted(source_counts.items()))}",
    ]
    if failures:
        lines.append(f"  failures: {len(failures)}  ({'; '.join(failures)})")
    if store_error:
        lines.append(f"  store   : FAILED - {store_error}")
    lines.append("-" * 60)
    print("\n" + "\n".join(lines))

    # Write a run log file when asked (the cron workflow sets BASR_RUN_LOG_DIR
    # so the run log is uploaded as a workflow artifact).
    log_dir = os.environ.get("BASR_RUN_LOG_DIR")
    if log_dir:
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, f"basr_{started_at:%Y%m%d_%H%M%S}.log")
            with open(log_path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            print(f"[+] Run log written: {log_path}")
        except OSError as exc:
            print(f"[-] Could not write run log: {exc}")

    if dry_run:
        return 0
    # Exit non-zero only if the store itself failed (nothing persisted) - a
    # failed source is normal drift, handled by design.
    return 1 if (store_error or status == "failed") else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="BASR ingestion pipeline")
    parser.add_argument("--limit", type=int, default=None, help="max docs per source")
    parser.add_argument("--dry-run", action="store_true", help="fetch only, no DB writes")
    parser.add_argument("--nlp", action="store_true", help="run NLP classification after ingestion")
    parser.add_argument("--nlp-limit", type=int, default=None, help="max docs to classify")
    parser.add_argument("--intel", action="store_true",
                        help="run the Phase 4 early-warning stage after ingestion")
    parser.add_argument("--agents", action="store_true",
                        help="run the Phase 5 agents stage (scheduled reports) after ingestion")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_pipeline(limit=args.limit, dry_run=args.dry_run,
                                              nlp=args.nlp, nlp_limit=args.nlp_limit,
                                              intel=args.intel, agents=args.agents)))


if __name__ == "__main__":
    main()
