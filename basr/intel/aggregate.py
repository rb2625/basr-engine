"""Time-series aggregation (Phase 4, Amendment A11).

Builds the ``time_series`` table from raw_docs + classifications + the topic
and entity link tables, in five dimensions:

- ``global``    - every doc (dimension_id 0 - a sentinel, NOT NULL: Postgres
                  treats NULL as distinct in UNIQUE constraints, so NULL
                  dimension_ids would never dedupe on upsert)
- ``topic``     - per topic (topics.id)
- ``sector``    - per classification.sector, backed by entity rows of type
                  'sector' so the schema's UNIQUE constraint stays intact
- ``emirate``   - per location entity (entities.id where type = 'location')

Hourly rows cover the last 48h (intraday spikes); daily rows cover the last
45 days (anomaly engine). All buckets are UTC. Sentiment stats are computed
only over classified docs in the bucket; buckets with no classifications get
NULL sentiment.

The pass is deterministic and zero-cost (no LLM): it re-reads the derived
tables and upserts idempotently on
(bucket_start, granularity, dimension_type, dimension_id).
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from ..store.store import SupabaseStore

DAYS_BACK = 45
HOURS_BACK = 48

# Sectors become entity rows of type 'sector' (schema's entities.type allows
# it) so dimension_id can reference them instead of overloading NULL.
SECTOR_ENTITY_TYPE = "sector"


def _utc(ts: str | None) -> datetime:
    d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return d.astimezone(timezone.utc)


def _day_start(d: datetime) -> datetime:
    return d.replace(hour=0, minute=0, second=0, microsecond=0)


def _hour_start(d: datetime) -> datetime:
    return d.replace(minute=0, second=0, microsecond=0)


async def _fetch_inputs(store: SupabaseStore) -> dict[str, Any]:
    """Pull the derived tables needed to aggregate. Never raises: on any
    missing table the caller degrades (working rule 3)."""
    out: dict[str, Any] = {}

    docs = await store._with_retry(
        lambda: store._client.table("raw_docs")
        .select("id,published_at,fetched_at").limit(100000).execute()
    )
    out["docs"] = docs.data or []

    cl = await store._with_retry(
        lambda: store._client.table("classifications")
        .select("raw_doc_id,sentiment_score,signal_type,sector")
        .limit(100000).execute()
    )
    out["classifications"] = cl.data or []

    dt = await store._with_retry(
        lambda: store._client.table("doc_topics").select("doc_id,topic_id")
        .limit(100000).execute()
    )
    out["doc_topics"] = dt.data or []

    tp = await store._with_retry(
        lambda: store._client.table("topics").select("id,key").limit(100000).execute()
    )
    out["topics"] = tp.data or []

    de = await store._with_retry(
        lambda: store._client.table("doc_entities").select("doc_id,entity_id")
        .limit(100000).execute()
    )
    out["doc_entities"] = de.data or []

    en = await store._with_retry(
        lambda: store._client.table("entities")
        .select("id,type,normalized").limit(100000).execute()
    )
    out["entities"] = en.data or []

    return out


def _stats(scores: list[float]) -> tuple[float | None, float | None]:
    if not scores:
        return None, None
    n = len(scores)
    mean = sum(scores) / n
    if n < 2:
        return round(mean, 4), None
    var = sum((s - mean) ** 2 for s in scores) / (n - 1)
    return round(mean, 4), round(math.sqrt(var), 4)


async def build_time_series(
    store: SupabaseStore, *, days: int = DAYS_BACK, hours: int = HOURS_BACK
) -> int:
    """Recompute daily (last ``days``) + hourly (last ``hours``) buckets and
    upsert them. Returns the number of rows written."""
    data = await _fetch_inputs(store)
    docs = data["docs"]
    if not docs:
        return 0

    now = datetime.now(timezone.utc)
    day_cutoff = _day_start(now) - timedelta(days=days - 1)
    hour_cutoff = _hour_start(now) - timedelta(hours=hours - 1)

    # Sector entity ids: upsert once, then reference.
    sector_ids: dict[str, int] = {}
    sectors_present = sorted({
        c.get("sector") for c in data["classifications"]
        if c.get("sector") and c["sector"] != "General"
    })
    if sectors_present:
        rows = [{"name": s, "type": SECTOR_ENTITY_TYPE, "normalized": s.lower(),
                 "lat": None, "lng": None,
                 "metadata": {"gazetteer": True, "sector": True}}
                for s in sectors_present]
        await store._with_retry(
            lambda: store._client.table("entities")
            .upsert(rows, ignore_duplicates=True, on_conflict="type,normalized")
            .execute()
        )
        fetched = await store._with_retry(
            lambda: store._client.table("entities")
            .select("id,normalized").eq("type", SECTOR_ENTITY_TYPE).execute()
        )
        sector_ids = {r["normalized"]: r["id"] for r in (fetched.data or [])}

    topic_ids = {r["id"]: r["key"] for r in data["topics"]}
    location_ids = {r["id"]: r["normalized"] for r in data["entities"]
                    if r.get("type") == "location"}

    # doc -> (day, hour) timestamps
    doc_ts: dict[int, tuple[datetime, datetime]] = {}
    for d in docs:
        raw = d.get("published_at") or d.get("fetched_at")
        if not raw:
            continue
        ts = _utc(raw)
        doc_ts[d["id"]] = (_day_start(ts), _hour_start(ts))

    # doc -> sentiment score + sector
    doc_sent: dict[int, float] = {}
    doc_sector: dict[int, str] = {}
    for c in data["classifications"]:
        rid = c.get("raw_doc_id")
        score = c.get("sentiment_score")
        if rid and score is not None:
            doc_sent[rid] = float(score)
        if rid and c.get("sector"):
            doc_sector[rid] = c["sector"]

    # dim_type -> dim_id -> doc_id set
    topic_docs: dict[int, set[int]] = defaultdict(set)
    for l in data["doc_topics"]:
        if l.get("doc_id") and l.get("topic_id"):
            topic_docs[l["topic_id"]].add(l["doc_id"])
    entity_docs: dict[int, set[int]] = defaultdict(set)
    for l in data["doc_entities"]:
        if l.get("doc_id") and l.get("entity_id"):
            entity_docs[l["entity_id"]].add(l["doc_id"])

        # Global sentinel dimension_id (0, not NULL - see module docstring).
    GLOBAL_ID = 0

    # bucket key: (granularity, dim_type, dim_id, start_iso) -> sent scores
    buckets: dict[tuple, list[float]] = defaultdict(list)
    for doc_id, (day, hour) in doc_ts.items():
        if day >= day_cutoff:
            buckets[("day", "global", GLOBAL_ID, day.isoformat())].append(doc_id)
            buckets[("hour", "global", GLOBAL_ID, hour.isoformat())].append(doc_id)
        if day >= day_cutoff:
            for tid in topic_docs:
                if doc_id in topic_docs[tid]:
                    buckets[("day", "topic", tid, day.isoformat())].append(doc_id)
            for eid in entity_docs:
                if doc_id in entity_docs[eid] and eid in location_ids:
                    buckets[("day", "emirate", eid, day.isoformat())].append(doc_id)
            sec = doc_sector.get(doc_id)
            if sec and sec != "General":
                sid = sector_ids.get(sec.lower())
                if sid:
                    buckets[("day", "sector", sid, day.isoformat())].append(doc_id)
        if hour >= hour_cutoff:
            buckets[("hour", "global", None, hour.isoformat())].append(doc_id)

    # Assemble rows (hourly rows only for global to keep the table lean).
    rows: list[dict] = []
    for (gran, dim_type, dim_id, start_iso), doc_ids in buckets.items():
        if gran == "hour" and dim_type != "global":
            continue
        start = datetime.fromisoformat(start_iso)
        end = start + timedelta(hours=1 if gran == "hour" else 1)
        scores = [doc_sent[d] for d in doc_ids if d in doc_sent]
        avg, std = _stats(scores)
        rows.append({
            "bucket_start": start.isoformat(),
            "bucket_end": end.isoformat(),
            "granularity": gran,
            "dimension_type": dim_type,
            "dimension_id": dim_id,
            "volume": len(doc_ids),
            "sentiment_avg": avg,
            "sentiment_std": std,
        })

    written = 0
    if rows:
        for i in range(0, len(rows), 100):
            batch = rows[i : i + 100]
            resp = await store._with_retry(
                lambda b=batch: store._client.table("time_series")
                .upsert(b, ignore_duplicates=True,
                        on_conflict="bucket_start,granularity,dimension_type,dimension_id")
                .execute()
            )
            written += len(resp.data or [])
    return written
