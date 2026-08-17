"""Alerts (Phase 4): creation, lifecycle, and delivery.

- ``create_alerts`` turns anomaly records into ``alerts`` rows, deduped by
  the open-alert check (a bucket alerts once, not every cron run).
- ``deliver_alerts`` sends pending alerts over the configured channels
  (Telegram bot + Resend email) and records the outcome on the row.
- Lifecycle: open -> acknowledged / dismissed / promoted. Status changes
  are simple store updates (the org console UI lands in Phase 5).

Delivery is strictly additive: when a channel's key is not configured the
alert is marked ``skipped`` and stays visible in the dashboard - the platform
never fails because a channel is missing (working rule 3).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from ..config import get_settings
from ..store.store import SupabaseStore

TIMEOUT_S = 10


def _fmt_text(a: dict) -> str:
    """Format an alert for delivery. Works for both anomaly-shaped dicts
    (with dimension_label / score / z / stl) and alert-table rows (title +
    evidence only)."""
    date = (a.get("bucket_start") or "")[:10]
    headline = a.get("dimension_label") or a.get("title", "BASR early warning")
    lines = [f"BASR early warning [{a.get('severity', 'medium').upper()}]", str(headline)]
    if a.get("volume") is not None and date:
        lines.append(f"{a['volume']} docs on {date}")
    if a.get("score") is not None:
        lines.append(f"score {a['score']} (z {a['z']}, stl {a['stl_z']})")
    for e in a.get("evidence", [])[:3]:
        lines.append(f"- {e.get('title', '(untitled)')[:90]} ({e.get('source', '')})")
    return "\n".join(lines)


async def create_alerts(store: SupabaseStore, anomalies: list[dict]) -> int:
    """Insert one alert per anomaly, unless an open alert already exists for
    the same bucket. Returns the number of new alerts."""
    created = 0
    for a in anomalies:
        existing = await store._with_retry(
            lambda a=a: store._client.table("alerts")
            .select("id").eq("time_series_id", a["time_series_id"])
            .in_("status", ["open", "acknowledged", "promoted"])
            .limit(1)
            .execute()
        )
        if existing.data:
            continue
        row = {
            "time_series_id": a["time_series_id"],
            "title": f"{a['dimension_label']} spike - {a['volume']} docs",
            "severity": a["severity"],
            "status": "open",
            "evidence": a.get("evidence", []),
        }
        await store._with_retry(
            lambda row=row: store._client.table("alerts").insert(row).execute()
        )
        created += 1
    return created


async def deliver_alerts(store: SupabaseStore, alerts: list[dict] | None = None) -> int:
    """Deliver pending alerts over every configured channel. Returns the
    number of successful deliveries. Never raises for channel failures."""
    if alerts is None:
        try:
            resp = await store._with_retry(
                lambda: store._client.table("alerts")
                .select("id,title,severity,evidence,time_series_id")
                .eq("delivery_status", "pending")
                .limit(50)
                .execute()
            )
        except Exception as exc:
            if getattr(exc, "code", "") != "42703":
                raise
            # Delivery columns not in the live schema yet (schema.sql not
            # re-run) - degrade to delivering every open alert without
            # tracking (Amendment A11).
            print("    [-] delivery columns missing - delivering open alerts "
                  "without tracking (re-run schema.sql for the permanent fix)")
            resp = await store._with_retry(
                lambda: store._client.table("alerts")
                .select("id,title,severity,evidence,time_series_id")
                .eq("status", "open")
                .limit(50)
                .execute()
            )
        alerts = resp.data or []
    if not alerts:
        return 0
    tracking = await _has_delivery_columns(store)

    settings = get_settings()
    telegram = bool(settings.telegram_bot_token and settings.telegram_chat_id)
    email = bool(settings.resend_api_key and settings.alert_email_to)

    sent = 0
    for a in alerts:
        text = _fmt_text({**a, "bucket_start": await _bucket_start(store, a)})
        ok_channels: list[str] = []
        if telegram:
            ok = await _send_telegram(
                settings.telegram_bot_token or "", settings.telegram_chat_id or "", text
            )
            if ok:
                ok_channels.append("telegram")
        if email:
            ok = await _send_resend(
                settings.resend_api_key or "",
                settings.alert_email_from or "BASR <alerts@basr.ae>",
                settings.alert_email_to or "",
                f"BASR early warning: {a['title']}",
                text,
            )
            if ok:
                ok_channels.append("email")

        status = "sent" if ok_channels else ("skipped" if not (telegram or email)
                                             else "failed")
        channel = ok_channels[0] if ok_channels else None
        if tracking:
            await store._with_retry(
                lambda a=a, status=status, channel=channel: store._client
                .table("alerts")
                .update({
                    "delivery_status": status,
                    "channel": channel,
                    "delivered_at": datetime.now(timezone.utc).isoformat()
                    if status == "sent" else None,
                })
                .eq("id", a["id"])
                .execute()
            )
        if status == "sent":
            sent += 1
    return sent


async def _has_delivery_columns(store: SupabaseStore) -> bool:
    """True when the alerts table has the A11 delivery columns (schema.sql
    re-run). Cached per process via the module global below."""
    global _DELIVERY_COLUMNS_OK
    if _DELIVERY_COLUMNS_OK is not None:
        return _DELIVERY_COLUMNS_OK
    try:
        await store._with_retry(
            lambda: store._client.table("alerts")
            .select("delivery_status").limit(1).execute()
        )
        _DELIVERY_COLUMNS_OK = True
    except Exception as exc:
        _DELIVERY_COLUMNS_OK = getattr(exc, "code", "") != "42703"
    return _DELIVERY_COLUMNS_OK


_DELIVERY_COLUMNS_OK: bool | None = None


async def _bucket_start(store: SupabaseStore, a: dict) -> str:
    if not a.get("time_series_id"):
        return ""
    try:
        resp = await store._with_retry(
            lambda: store._client.table("time_series")
            .select("bucket_start").eq("id", a["time_series_id"]).limit(1).execute()
        )
        return (resp.data or [{}])[0].get("bucket_start", "")
    except Exception:
        return ""


async def _send_telegram(token: str, chat_id: str, text: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            r = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text[:4000]},
            )
        return r.status_code == 200
    except Exception as exc:
        print(f"    [-] telegram delivery failed: {str(exc)[:120]}")
        return False


async def _send_resend(api_key: str, from_email: str, to: str, subject: str, text: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"from": from_email, "to": [to], "subject": subject, "text": text},
            )
        return r.status_code == 200
    except Exception as exc:
        print(f"    [-] email delivery failed: {str(exc)[:120]}")
        return False


async def set_alert_status(store: SupabaseStore, alert_id: int, status: str) -> bool:
    """Lifecycle: acknowledged / dismissed / promoted. Never raises."""
    try:
        await store._with_retry(
            lambda: store._client.table("alerts")
            .update({"status": status}).eq("id", alert_id).execute()
        )
        return True
    except Exception as exc:
        print(f"    [-] alert status update failed: {str(exc)[:120]}")
        return False
