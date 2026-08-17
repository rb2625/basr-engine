"""Issue brief generator (Phase 5, A12; plan sec 8.1).

Turns an alert into a decision-ready brief: what/where/who, sentiment
trajectory, top evidence with links, severity (impact x urgency x spread),
and ordered recommended responses for the owning org. One LLM call for the
narrative; a deterministic data-built brief is the fallback when the daily
token budget is exhausted or the model fails (working rule 3).

The human-in-the-loop flow (plan sec 7): an analyst promotes an open alert
into a brief with ``python -m basr.agents --brief <alert_id>``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..store import SupabaseStore
from .llm import AgentLLM
from .severity import justify_severity, score_severity


# ---------------------------------------------------------------------------
# Evidence gathering
# ---------------------------------------------------------------------------

async def _load_alert(store: SupabaseStore, alert_id: int) -> dict | None:
    try:
        resp = await store._with_retry(
            lambda: store._client.table("alerts")
            .select("*").eq("id", alert_id).limit(1).execute()
        )
    except Exception as exc:
        print(f"    [-] alert load failed: {str(exc)[:120]}")
        return None
    rows = resp.data or []
    return rows[0] if rows else None


async def _load_bucket(store: SupabaseStore, ts_id: int | None) -> dict | None:
    if not ts_id:
        return None
    try:
        resp = await store._with_retry(
            lambda: store._client.table("time_series")
            .select("*").eq("id", ts_id).limit(1).execute()
        )
    except Exception as exc:
        print(f"    [-] bucket load failed: {str(exc)[:120]}")
        return None
    rows = resp.data or []
    return rows[0] if rows else None


async def _fetch_evidence(store: SupabaseStore, bucket: dict,
                          limit: int = 25) -> list[dict]:
    """Docs inside the flagged bucket, joined with classifications + topics +
    entities. Never raises; returns [] on any failure."""
    try:
        start = datetime.fromisoformat(
            bucket["bucket_start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(
            bucket["bucket_end"].replace("Z", "+00:00"))
        resp = await store._with_retry(
            lambda: store._client.table("raw_docs")
            .select("id,title,source,url,published_at")
            .gte("published_at", start.isoformat())
            .lt("published_at", end.isoformat())
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        docs = resp.data or []
    except Exception as exc:
        print(f"    [-] evidence fetch failed: {str(exc)[:120]}")
        return []
    if not docs:
        return []

    ids = [d["id"] for d in docs]
    try:
        cls = await store._with_retry(
            lambda: store._client.table("classifications")
            .select("raw_doc_id,sentiment_label,signal_type,intensity_score,"
                    "confidence,model_version")
            .in_("raw_doc_id", ids).execute()
        )
        topics = await store._with_retry(
            lambda: store._client.table("doc_topics")
            .select("doc_id,topic_id").in_("doc_id", ids).execute()
        )
        ents = await store._with_retry(
            lambda: store._client.table("doc_entities")
            .select("doc_id,entity_id,role").in_("doc_id", ids).execute()
        )
    except Exception as exc:
        print(f"    [-] evidence enrich failed: {str(exc)[:120]}")
        cls = topics = ents = []

    topic_ids = {t["topic_id"] for t in (topics.data or [])}
    ent_ids = {e["entity_id"] for e in (ents.data or [])}
    topic_names: dict[int, str] = {}
    ent_names: dict[int, str] = {}
    try:
        if topic_ids:
            tr = await store._with_retry(
                lambda: store._client.table("topics")
                .select("id,label_en").in_("id", list(topic_ids)).execute())
            topic_names = {t["id"]: t["label_en"] for t in (tr.data or [])}
        if ent_ids:
            er = await store._with_retry(
                lambda: store._client.table("entities")
                .select("id,name,type").in_("id", list(ent_ids)).execute())
            ent_names = {e["id"]: e["name"] for e in (er.data or [])}
    except Exception:
        pass

    cls_by_doc: dict[int, dict] = {}
    for c in (cls.data or []):
        cls_by_doc[c["raw_doc_id"]] = c
    topics_by_doc: dict[int, list[str]] = {}
    for t in (topics.data or []):
        topics_by_doc.setdefault(t["doc_id"], []).append(
            topic_names.get(t["topic_id"], f"topic-{t['topic_id']}"))
    ents_by_doc: dict[int, list[str]] = {}
    for e in (ents.data or []):
        ents_by_doc.setdefault(e["doc_id"], []).append(
            ent_names.get(e["entity_id"], f"entity-{e['entity_id']}"))

    for d in docs:
        c = cls_by_doc.get(d["id"], {})
        d["sentiment"] = c.get("sentiment_label")
        d["signal"] = c.get("signal_type")
        d["intensity"] = c.get("intensity_score")
        d["topics"] = topics_by_doc.get(d["id"], [])
        d["entities"] = ents_by_doc.get(d["id"], [])
        d["text"] = (d.get("title") or "(untitled)")[:180]
    return docs


async def _trajectory(store: SupabaseStore, bucket: dict, days: int = 14
                      ) -> list[dict]:
    """Daily volume/sentiment for the same dimension, for the trajectory."""
    dimension = bucket.get("dimension_type", "global")
    dim_id = bucket.get("dimension_id", 0)
    try:
        resp = await store._with_retry(
            lambda: store._client.table("time_series")
            .select("bucket_start,volume,sentiment_avg,anomaly_flag")
            .eq("granularity", "day")
            .eq("dimension_type", dimension)
            .eq("dimension_id", dim_id)
            .order("bucket_start", desc=True)
            .limit(days)
            .execute()
        )
        rows = list(reversed(resp.data or []))
        return [{
            "date": r["bucket_start"][:10],
            "volume": r["volume"],
            "sentiment_avg": r.get("sentiment_avg"),
            "flag": bool(r.get("anomaly_flag")),
        } for r in rows]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Stats + brief assembly
# ---------------------------------------------------------------------------

def _stats(docs: list[dict], bucket: dict, prev_volume: float) -> dict:
    n = len(docs)
    stress = sum(1 for d in docs if d.get("signal") == "stress")
    neg = sum(1 for d in docs if d.get("sentiment") == "negative")
    sources = {d.get("source") for d in docs if d.get("source")}
    ents = {e for d in docs for e in (d.get("entities") or [])}
    topics = {t for d in docs for t in (d.get("topics") or [])}
    return {
        "volume": bucket.get("volume") or n,
        "prev_volume": prev_volume,
        "stress_share": (stress + 0.5 * neg) / n if n else 0.0,
        "n_sources": len(sources),
        "n_entities": len(ents),
        "n_emirates": len({e for d in docs for e in (d.get("entities") or [])
                           if "emirate" in e.lower()}),
        "n_topics": len(topics),
    }


async def _prev_volume(store: SupabaseStore, bucket: dict) -> float:
    """Volume of the bucket immediately before this one (same dimension)."""
    try:
        resp = await store._with_retry(
            lambda: store._client.table("time_series")
            .select("volume")
            .eq("granularity", bucket.get("granularity", "day"))
            .eq("dimension_type", bucket.get("dimension_type", "global"))
            .eq("dimension_id", bucket.get("dimension_id", 0))
            .lt("bucket_start", bucket["bucket_start"])
            .order("bucket_start", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        return float(rows[0]["volume"]) if rows else 0.0
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# LLM brief
# ---------------------------------------------------------------------------

_BRIEF_SYSTEM = (
    "You are a senior analyst writing an intelligence brief for UAE "
    "universities, government entities, and brand teams. You are given: a "
    "detected signal surge (anomaly), its evidence documents, its sentiment "
    "trajectory, and a computed severity. Write a brief that an analyst can "
    "act on. STRICT RULES: (1) every claim must trace to the provided "
    "evidence - never invent facts, numbers, quotes, or sources; (2) if "
    "evidence is thin, say so honestly; (3) respond in strict JSON with "
    "exactly these keys: title (string), summary (2-3 sentences), what "
    "(string), where (string, or 'UAE-wide' if none), who (string), "
    "trajectory (1-2 sentences on trend), recommended_response (array of "
    "objects {action, owner, rationale}, 2-4 items, ordered by priority). "
    "Reply with ONLY the JSON object."
)


def _fallback_brief(alert: dict, bucket: dict, docs: list[dict],
                    severity: dict, traj: list[dict]) -> dict:
    """Deterministic brief used when the LLM is unavailable."""
    where = sorted({e for d in docs for e in (d.get("entities") or [])
                    if "emirate" in e.lower()}) or ["UAE-wide"]
    who = sorted({e for d in docs for e in (d.get("entities") or [])
                  if "emirate" not in e.lower()})[:5]
    top = docs[:3]
    return {
        "title": alert.get("title", "UAE signal surge"),
        "summary": (
            f"Volume spike of {severity['factors']['volume']} docs "
            f"({severity['level']} severity, score {severity['score']:.2f}) "
            f"with {severity['factors']['stress_share'] * 100:.0f}% "
            f"stress-classified signals. Auto-generated brief from detected "
            f"anomaly; verify with primary sources before action."
        ),
        "what": f"{severity['factors']['dimension']}-level signal surge",
        "where": ", ".join(where),
        "who": ", ".join(who) if who else "Unnamed entities",
        "trajectory": (
            f"{len(traj)} days of history; "
            + (f"peak {max(t['volume'] for t in traj)} docs/day."
               if traj else "insufficient history.")
        ),
        "recommended_response": [
            {"action": "Verify the surge against primary sources",
             "owner": "BASR analyst",
             "rationale": "Anomaly may reflect data quality, not reality"},
            {"action": "Notify sector stakeholders named in evidence",
             "owner": "Owning organization",
             "rationale": "Early, grounded awareness prevents escalation"},
            {"action": "Prepare a monitoring plan if the trend continues",
             "owner": "Owning organization",
             "rationale": "A second consecutive spike confirms a real shift"},
        ],
        "evidence": [{"title": d.get("title"), "url": d.get("url"),
                      "source": d.get("source")} for d in top],
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def build_brief(store: SupabaseStore, alert_id: int,
                      *, publish: bool = False, llm: AgentLLM | None = None
                      ) -> dict | None:
    """Build (and store) a brief for an alert. Returns the brief row dict."""
    alert = await _load_alert(store, alert_id)
    if not alert:
        print(f"    [-] alert {alert_id} not found")
        return None
    bucket = await _load_bucket(store, alert.get("time_series_id"))
    if not bucket:
        bucket = {"bucket_start": datetime.now(timezone.utc).isoformat(),
                  "bucket_end": datetime.now(timezone.utc).isoformat(),
                  "dimension_type": "global", "dimension_id": 0,
                  "granularity": "day", "volume": 0}

    docs = await _fetch_evidence(store, bucket)
    traj = await _trajectory(store, bucket)
    prev = await _prev_volume(store, bucket)

    ctx = _stats(docs, bucket, prev)
    ctx["dimension"] = bucket.get("dimension_type", "global")
    ctx["anomaly_severity"] = alert.get("severity", "medium")
    ctx["recent"] = 1.0 if docs else 0.0
    sev = score_severity(ctx)

    if llm is None:
        llm = AgentLLM()
    justification = justify_severity(sev, llm)
    sev["justification"] = justification

    # Build the LLM input: compact, grounded context.
    evidence_lines = "\n".join(
        f"- [{d.get('source')}] {d.get('text')} "
        f"(signal={d.get('signal')}, sentiment={d.get('sentiment')}) "
        f"url={d.get('url')}"
        for d in docs[:15]
    ) or "- (no evidence documents in the bucket window)"
    traj_lines = "\n".join(
        f"- {t['date']}: vol={t['volume']} sent={t['sentiment_avg']}"
        + (" ANOMALY" if t["flag"] else "")
        for t in traj
    ) or "- (no trajectory history)"

    user = (
        f"ALERT: {alert.get('title')}\n"
        f"SEVERITY: {sev['level']} (score {sev['score']})\n"
        f"JUSTIFICATION: {justification}\n\n"
        f"DIMENSION: {bucket.get('dimension_type')} "
        f"(id {bucket.get('dimension_id')})\n\n"
        f"EVIDENCE DOCS (top {min(len(docs), 15)}):\n{evidence_lines}\n\n"
        f"TRAJECTORY (daily):\n{traj_lines}"
    )
    data = llm.ask(_BRIEF_SYSTEM, user, max_tokens=1600)
    brief = _fallback_brief(alert, bucket, docs, sev, traj) if data is None \
        else data

    # Normalize the brief into the DB shape, tolerating LLM field drift.
    rec = {
        "alert_id": alert["id"],
        "org_id": None,
        "title": str(brief.get("title") or alert.get("title")
                     or "UAE signal surge")[:300],
        "summary": str(brief.get("summary") or
                       _fallback_brief(alert, bucket, docs, sev,
                                       traj)["summary"]),
        "severity": sev["level"],
        "recommended_response": brief.get("recommended_response")
        or _fallback_brief(alert, bucket, docs, sev, traj)["recommended_response"],
        "evidence": brief.get("evidence")
        or [{"title": d.get("title"), "url": d.get("url"),
             "source": d.get("source")} for d in docs[:5]],
        "status": "published" if publish else "draft",
        "model_version": "basr-agents-v1",
    }
    # Keep the severity justification attached to the evidence for the UI.
    rec["evidence"] = rec["evidence"] + [{"severity_justification": justification,
                                          "severity_score": sev["score"],
                                          "trajectory": traj}]

    try:
        await store._with_retry(
            lambda: store._client.table("briefs").insert(rec).execute()
        )
    except Exception as exc:
        print(f"    [-] brief insert failed: {str(exc)[:150]}")
        return None
    print(f"    [+] brief built: {rec['title']} "
          f"[{sev['level']}, severity score {sev['score']:.2f}]")
    return rec
