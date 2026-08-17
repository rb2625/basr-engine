"""Scheduled reports (Phase 5, A12; plan sec 8.4).

Daily "UAE Pulse" and weekly sector digest built from time_series + alerts.
The narrative comes from one LLM call with a data-built fallback (working
rule 3). Reports land in the ``reports`` table (schema sec 4) and are
delivered over the Phase 4 channels (Telegram/email) - the same keys as
alerts, so one setup serves both.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..intel.alerts import _send_resend, _send_telegram
from ..store import SupabaseStore
from .llm import AgentLLM

_REPORT_SYSTEM = (
    "You are the editor of UAE Pulse, a daily economic-intelligence digest "
    "for universities, agencies, and government analysts. You are given the "
    "day's measured stats. Write a tight, honest narrative (2-4 sentences) "
    "plus 2-3 headline bullets. STRICT RULES: never invent numbers or facts "
    "beyond the input; if the data is thin, say so. Reply in strict JSON: "
    "{\"narrative\": \"...\", \"headlines\": [\"...\"]}. English only."
)


# ---------------------------------------------------------------------------
# Data gathering
# ---------------------------------------------------------------------------

async def _series(store: SupabaseStore, dimension_type: str,
                  dimension_id: int, since: datetime) -> list[dict]:
    try:
        resp = await store._with_retry(
            lambda: store._client.table("time_series")
            .select("bucket_start,volume,sentiment_avg,anomaly_flag")
            .eq("granularity", "day")
            .eq("dimension_type", dimension_type)
            .eq("dimension_id", dimension_id)
            .gte("bucket_start", since.isoformat())
            .order("bucket_start")
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        print(f"    [-] series fetch failed: {str(exc)[:120]}")
        return []


async def _dimension_rows(store: SupabaseStore, dimension_type: str,
                          since: datetime) -> list[dict]:
    """Aggregate time_series rows grouped by dimension_id over the window."""
    try:
        resp = await store._with_retry(
            lambda: store._client.table("time_series")
            .select("dimension_id,volume,sentiment_avg")
            .eq("granularity", "day")
            .eq("dimension_type", dimension_type)
            .gte("bucket_start", since.isoformat())
            .execute()
        )
    except Exception as exc:
        print(f"    [-] dimension rows failed: {str(exc)[:120]}")
        return []
    by_dim: dict[int, dict] = {}
    for r in (resp.data or []):
        d = by_dim.setdefault(r["dimension_id"],
                              {"dimension_id": r["dimension_id"],
                               "volume": 0, "sent_sum": 0.0, "sent_n": 0})
        d["volume"] += r["volume"]
        if r.get("sentiment_avg") is not None:
            d["sent_sum"] += float(r["sentiment_avg"])
            d["sent_n"] += 1
    out = []
    for d in by_dim.values():
        out.append({
            "dimension_id": d["dimension_id"],
            "volume": d["volume"],
            "sentiment_avg": round(d["sent_sum"] / d["sent_n"], 3)
            if d["sent_n"] else None,
        })
    return sorted(out, key=lambda r: r["volume"], reverse=True)


async def _dimension_label(store: SupabaseStore, dimension_type: str,
                           dimension_id: int) -> str:
    if dimension_id == 0:
        return "UAE (global)"
    try:
        if dimension_type == "topic":
            resp = await store._with_retry(
                lambda: store._client.table("topics")
                .select("label_en").eq("id", dimension_id).limit(1).execute())
            rows = resp.data or []
            return rows[0]["label_en"] if rows else f"topic-{dimension_id}"
        resp = await store._with_retry(
            lambda: store._client.table("entities")
            .select("name").eq("id", dimension_id).limit(1).execute())
        rows = resp.data or []
        return rows[0]["name"] if rows else f"{dimension_type}-{dimension_id}"
    except Exception:
        return f"{dimension_type}-{dimension_id}"


async def _open_alerts(store: SupabaseStore) -> int:
    try:
        resp = await store._with_retry(
            lambda: store._client.table("alerts")
            .select("id", count="exact").eq("status", "open").execute())
        return getattr(resp, "count", None) or len(resp.data or [])
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def _fmt_sent(v: float | None) -> str:
    if v is None:
        return "n/a"
    return f"{v:+.3f}"


async def _collect(store: SupabaseStore, days: int) -> dict:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    prior_since = since - timedelta(days=days)

    cur = await _series(store, "global", 0, since)
    prev = await _series(store, "global", 0, prior_since)
    topics = await _dimension_rows(store, "topic", since)
    sectors = await _dimension_rows(store, "sector", since)
    emirates = await _dimension_rows(store, "emirate", since)
    alerts_open = await _open_alerts(store)

    def vol(rows: list[dict]) -> int:
        return sum(r["volume"] for r in rows)

    def avg_sent(rows: list[dict]) -> float | None:
        vals = [r["sentiment_avg"] for r in rows if r.get("sentiment_avg")
                is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    topic_rows = [{
        "topic": await _dimension_label(store, "topic", t["dimension_id"]),
        "volume": t["volume"],
        "sentiment_avg": t["sentiment_avg"],
    } for t in topics[:6]]
    sector_rows = [{
        "sector": await _dimension_label(store, "sector", s["dimension_id"]),
        "volume": s["volume"],
        "sentiment_avg": s["sentiment_avg"],
    } for s in sectors[:8]]
    emirate_rows = [{
        "emirate": await _dimension_label(store, "emirate", e["dimension_id"]),
        "volume": e["volume"],
    } for e in emirates[:5]]

    return {
        "period_days": days,
        "current_volume": vol(cur),
        "prior_volume": vol(prev),
        "volume_delta_pct": round(
            (vol(cur) - vol(prev)) / vol(prev) * 100, 1) if vol(prev) else None,
        "sentiment_avg": avg_sent(cur),
        "sentiment_prior": avg_sent(prev),
        "anomaly_flags": sum(1 for r in cur if r.get("anomaly_flag")),
        "open_alerts": alerts_open,
        "top_topics": topic_rows,
        "top_sectors": sector_rows,
        "top_emirates": emirate_rows,
    }


def _fallback_narrative(stats: dict) -> dict:
    delta = stats["volume_delta_pct"]
    trend = f"up {delta:.0f}%" if delta is not None and delta >= 0 \
        else ("down" if delta is not None else "flat")
    return {
        "narrative": (
            f"UAE Pulse: {stats['current_volume']} docs in the last "
            f"{stats['period_days']} days ({trend} vs the prior period), "
            f"mean sentiment {_fmt_sent(stats['sentiment_avg'])} "
            f"({_fmt_sent(stats['sentiment_prior'])} prior), "
            f"{stats['anomaly_flags']} anomaly flags and "
            f"{stats['open_alerts']} open alerts. Auto-generated; "
            f"verify with primary sources."
        ),
        "headlines": [
            f"Volume {'+' if delta and delta >= 0 else ''}{delta:.0f}% "
            f"vs prior {stats['period_days']}-day window"
            if delta is not None else "Volume steady vs prior window",
            f"Top topic: {stats['top_topics'][0]['topic']}"
            if stats["top_topics"] else "No topic data yet",
            f"{stats['open_alerts']} open alerts requiring attention",
        ],
    }


async def build_report(store: SupabaseStore, kind: str = "daily",
                       *, llm: AgentLLM | None = None,
                       dry_run: bool = False) -> dict | None:
    """Build and store one scheduled report. Returns the row dict or None.
    With dry_run=True, everything is computed and printed but nothing is
    written (used by the orchestrator's dry-run mode)."""
    if kind not in ("daily", "weekly"):
        print(f"    [-] unknown report kind: {kind}")
        return None
    days = 1 if kind == "daily" else 7
    stats = await _collect(store, days)

    if dry_run:
        narrative = _fallback_narrative(stats)
    else:
        if llm is None:
            llm = AgentLLM()
        user = "Stats (JSON):\n" + str({k: v for k, v in stats.items()
                                        if k not in ("top_topics", "top_sectors",
                                                     "top_emirates")})
        data = llm.ask(_REPORT_SYSTEM, user, max_tokens=900)
        narrative = data if data else _fallback_narrative(stats)

    now = datetime.now(timezone.utc)
    period_start = (now - timedelta(days=days)).date()
    period_end = now.date()
    if kind == "daily":
        title = f"UAE Pulse - {period_end.isoformat()}"
    else:
        title = f"Weekly sector digest - {period_start.isoformat()} to " \
                f"{period_end.isoformat()}"

    body = {
        "narrative": narrative.get("narrative", ""),
        "headlines": narrative.get("headlines", []),
        "stats": stats,
    }
    row = {
        "kind": kind,
        "org_id": None,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "title": title,
        "body": body,
        "pdf_url": None,
        "model_version": "basr-agents-v1",
        "delivery_status": "pending",
    }
    if dry_run:
        print(f"    [dry-run] report computed, not stored: {title}")
        return row
    try:
        await store._with_retry(
            lambda: store._client.table("reports").insert(row).execute()
        )
    except Exception as exc:
        print(f"    [-] report insert failed (is the reports table live? "
              f"re-run schema.sql): {str(exc)[:120]}")
        return None
    print(f"    [+] report stored: {title}")
    return row


# ---------------------------------------------------------------------------
# Delivery (reuses the Phase 4 channel helpers)
# ---------------------------------------------------------------------------

async def deliver_reports(store: SupabaseStore) -> int:
    """Deliver pending reports over Telegram/email. Returns count sent."""
    from ..config import get_settings
    try:
        resp = await store._with_retry(
            lambda: store._client.table("reports")
            .select("*").eq("delivery_status", "pending").execute())
    except Exception as exc:
        print(f"    [-] reports delivery unavailable: {str(exc)[:120]}")
        return 0
    rows = resp.data or []
    if not rows:
        return 0

    settings = get_settings()
    telegram = bool(settings.telegram_bot_token and settings.telegram_chat_id)
    email = bool(settings.resend_api_key and settings.alert_email_to)
    sent = 0
    for r in rows:
        body = r.get("body") or {}
        narrative = body.get("narrative", "")
        headlines = "\n".join(f"  - {h}" for h in (body.get("headlines") or []))
        text = f"{r['title']}\n\n{narrative}\n{headlines}"
        ok: list[str] = []
        if telegram:
            if await _send_telegram(settings.telegram_bot_token or "",
                                    settings.telegram_chat_id or "", text):
                ok.append("telegram")
        if email:
            if await _send_resend(settings.resend_api_key or "",
                                  settings.alert_email_from
                                  or "BASR <alerts@basr.ae>",
                                  settings.alert_email_to or "",
                                  f"BASR report: {r['title']}", text):
                ok.append("email")
        status = "sent" if ok else ("skipped" if not (telegram or email)
                                    else "failed")
        channel = ok[0] if ok else None
        try:
            await store._with_retry(
                lambda r=r, status=status, channel=channel: store._client
                .table("reports")
                .update({
                    "delivery_status": status,
                    "channel": channel,
                    "delivered_at": datetime.now(timezone.utc).isoformat()
                    if status == "sent" else None,
                })
                .eq("id", r["id"])
                .execute()
            )
        except Exception:
            pass
        if status == "sent":
            sent += 1
    return sent
