"""Anomaly detection (Phase 4): rolling z-score + STL ensemble.

Flags volume spikes in the daily ``time_series`` rows. The ensemble is
deliberately conservative so a single day of slightly higher ingestion is
never a "spike":

- rolling z-score over a trailing window (WINDOW days) - works on sparse data
- STL residual z-score once enough history exists (STL_MIN_DAYS) - removes
  day-of-week seasonality (weekend dips, Monday news cycles)
- volume floor (MIN_VOLUME) - a one-off mention is not an anomaly
- final score = max(z, stl_z); flag when score >= Z_THRESHOLD

Flagged buckets get ``anomaly_score`` + ``anomaly_flag`` on their
time_series row. New flags also create alert records (in ``alerts.py``),
deduped by the open-alert check so a spike alerts once, not every run.

Zero LLM tokens: pure statistics over the aggregated table.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ..store.store import SupabaseStore

MIN_VOLUME = 5
Z_THRESHOLD = 2.5
WINDOW = 14
STL_MIN_DAYS = 28
STL_PERIOD = 7


def _zscore(value: float, mean: float, std: float) -> float:
    if std <= 1e-9:
        return 0.0
    return (value - mean) / std


def _rolling_z(values: list[float]) -> list[float]:
    """Trailing-window z-score for each point (0 for the first WINDOW)."""
    out: list[float] = []
    for i, v in enumerate(values):
        if i < WINDOW:
            out.append(0.0)
            continue
        window = values[i - WINDOW : i]
        mean = sum(window) / len(window)
        var = sum((x - mean) ** 2 for x in window) / (len(window) - 1) if len(window) > 1 else 0.0
        out.append(_zscore(v, mean, var ** 0.5))
    return out


def _stl_residual_z(values: list[float]) -> list[float]:
    """STL residual z-scores (statsmodels). Returns zeros when history is too
    short or statsmodels is unavailable - the rolling z-score still covers it."""
    if len(values) < STL_MIN_DAYS:
        return [0.0] * len(values)
    try:
        from statsmodels.tsa.seasonal import STL  # heavy, lazy import
    except Exception:
        return [0.0] * len(values)
    try:
        res = STL(values, period=STL_PERIOD, robust=True).fit()
        resid = (res.resid).tolist()
    except Exception:
        return [0.0] * len(values)
    mean = sum(resid) / len(resid)
    var = sum((x - mean) ** 2 for x in resid) / (len(resid) - 1) if len(resid) > 1 else 0.0
    std = var ** 0.5
    return [_zscore(r, mean, std) for r in resid]


def severity_for(z: float, volume: int) -> str:
    if z >= 4.0 or (z >= 3.0 and volume >= 15):
        return "critical"
    if z >= 3.0:
        return "high"
    if z >= Z_THRESHOLD:
        return "medium"
    return "low"


def _dim_label(dim_type: str, dim_id: Any, id_to_key: dict) -> str:
    if dim_type == "global":
        return "UAE overall"
    if dim_type == "topic":
        return f"topic:{id_to_key.get('topic', {}).get(dim_id, dim_id)}"
    if dim_type == "emirate":
        return f"location:{id_to_key.get('emirate', {}).get(dim_id, dim_id)}"
    if dim_type == "sector":
        return f"sector:{id_to_key.get('sector', {}).get(dim_id, dim_id)}"
    return str(dim_id)


async def detect_anomalies(store: SupabaseStore) -> list[dict]:
    """Scan daily time_series rows, flag spikes, and return anomaly records
    (one per flagged bucket, with evidence populated)."""
    # Load the daily series + dimension key maps.
    resp = await store._with_retry(
        lambda: store._client.table("time_series")
        .select("id,bucket_start,dimension_type,dimension_id,volume,"
                "sentiment_avg,anomaly_score,anomaly_flag")
        .eq("granularity", "day")
        .gte("bucket_start", (datetime.now(timezone.utc) - timedelta(days=60)).isoformat())
        .order("bucket_start")
        .limit(100000)
        .execute()
    )
    rows = resp.data or []

    tp = await store._with_retry(
        lambda: store._client.table("topics").select("id,key").execute()
    )
    topic_key = {r["id"]: r["key"] for r in (tp.data or [])}
    en = await store._with_retry(
        lambda: store._client.table("entities")
        .select("id,type,normalized").in_("type", ["location", "sector"]).execute()
    )
    emirate_key = {r["id"]: r["normalized"] for r in (en.data or [])
                   if r["type"] == "location"}
    sector_key = {r["id"]: r["normalized"] for r in (en.data or [])
                  if r["type"] == "sector"}
    id_to_key = {"topic": topic_key, "emirate": emirate_key, "sector": sector_key}

    # Group by dimension, preserving chronological order.
    by_dim: dict[tuple[str, Any], list[dict]] = {}
    for r in rows:
        by_dim.setdefault((r["dimension_type"], r["dimension_id"]), []).append(r)

    anomalies: list[dict] = []
    for (dim_type, dim_id), series in by_dim.items():
        # Only scan dimensions with real coverage: at least WINDOW+1 buckets
        # (so the baseline is meaningful) or a non-trivial total volume.
        if len(series) < WINDOW + 1:
            continue
        values = [float(s["volume"] or 0) for s in series]
        zs = _rolling_z(values)
        stl_zs = _stl_residual_z(values)
        for i, row in enumerate(series):
            z = zs[i]
            stl_z = stl_zs[i]
            score = max(z, stl_z)
            volume = int(row["volume"] or 0)
            if score < Z_THRESHOLD or volume < MIN_VOLUME:
                continue
            anomalies.append({
                "time_series_id": row["id"],
                "bucket_start": row["bucket_start"],
                "dimension_type": dim_type,
                "dimension_id": dim_id,
                "dimension_label": _dim_label(dim_type, dim_id, id_to_key),
                "score": round(score, 3),
                "z": round(z, 3),
                "stl_z": round(stl_z, 3),
                "volume": volume,
                "severity": severity_for(score, volume),
                "sentiment_avg": row.get("sentiment_avg"),
            })

    # Write scores + flags back, and attach evidence for the flagged ones.
    for a in anomalies:
        await store._with_retry(
            lambda a=a: store._client.table("time_series")
            .update({"anomaly_score": a["score"], "anomaly_flag": True})
            .eq("id", a["time_series_id"])
            .execute()
        )
        a["evidence"] = await _evidence_docs(store, a)

    return anomalies


async def _evidence_docs(store: SupabaseStore, anomaly: dict) -> list[dict]:
    """Top docs inside the flagged bucket (latest first, capped)."""
    start = datetime.fromisoformat(anomaly["bucket_start"].replace("Z", "+00:00"))
    end = start + timedelta(days=1)
    try:
        resp = await store._with_retry(
            lambda: store._client.table("raw_docs")
            .select("id,title,source,url,published_at")
            .gte("published_at", start.isoformat())
            .lt("published_at", end.isoformat())
            .order("published_at", desc=True)
            .limit(3)
            .execute()
        )
    except Exception:
        return []
    return [{
        "id": r["id"], "title": r.get("title") or "(untitled)",
        "source": r.get("source"), "url": r.get("url"),
    } for r in (resp.data or [])]
