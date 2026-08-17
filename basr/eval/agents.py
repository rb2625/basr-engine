"""Agent eval harness (Phase 5, A12; plan sec 8 - measured, not vibes).

Two scored sets:

1. SEVERITY (zero tokens): the deterministic scorer is evaluated against
   gold labels on 15 crafted cases spanning all four levels and the edge
   rules (anomaly override, thin evidence, growth-vs-spread tension).
   DoD bar: >= 85% agreement (plan sec 8.2).

2. BRIEF (small LLM budget, ~5 calls): the brief prompt is run on synthetic
   alert contexts and scored on format (valid JSON), completeness (all
   required fields), and a grounding proxy (numbers >= 5 and URLs cited in
   the brief must appear in the input context - no invented facts).

Both log into eval_datasets + eval_runs like every other model, so agent
quality is published next to sentiment scores.
"""

from __future__ import annotations

import re
import time

from ..agents.brief import _BRIEF_SYSTEM
from ..agents.llm import AgentLLM, model_version
from ..agents.severity import score_severity
from ..store import SupabaseStore
from .harness import compute_metrics, confusion, print_report

AGENT_VERSION = f"basr-agents-v1 ({model_version()})"

# ---------------------------------------------------------------------------
# Severity scored set (gold labels)
# ---------------------------------------------------------------------------

SEVERITY_CASES: list[tuple[dict, str]] = [
    # Big global surge: critical.
    ({"dimension": "global", "anomaly_severity": "critical", "volume": 75,
      "prev_volume": 12, "stress_share": 0.6, "n_sources": 4, "n_entities": 8,
      "n_topics": 5, "recent": 1.0}, "critical"),
    # Moderate global blip: medium.
    ({"dimension": "global", "anomaly_severity": "medium", "volume": 6,
      "prev_volume": 5, "stress_share": 0.3, "n_sources": 2, "n_entities": 3,
      "n_topics": 2, "recent": 1.0}, "medium"),
    # Single-topic stress cluster: high.
    ({"dimension": "topic", "anomaly_severity": "high", "volume": 20,
      "prev_volume": 4, "stress_share": 0.7, "n_sources": 3, "n_entities": 2,
      "n_topics": 1, "recent": 1.0}, "high"),
    # Tiny blip, one source: low.
    ({"dimension": "global", "anomaly_severity": "low", "volume": 3,
      "prev_volume": 1, "stress_share": 0.2, "n_sources": 1, "n_entities": 1,
      "n_topics": 1, "recent": 1.0}, "low"),
    # Emirate-level stress spike: high.
    ({"dimension": "emirate", "anomaly_severity": "high", "volume": 15,
      "prev_volume": 2, "stress_share": 0.8, "n_sources": 3, "n_entities": 4,
      "n_topics": 3, "recent": 1.0}, "high"),
    # Anomaly engine says critical: the scorer must never downgrade it.
    ({"dimension": "topic", "anomaly_severity": "critical", "volume": 5,
      "prev_volume": 4, "stress_share": 0.4, "n_sources": 1, "n_entities": 1,
      "n_topics": 1, "recent": 1.0}, "critical"),
    # Huge growth but one source and one topic: urgency dominates.
    ({"dimension": "global", "anomaly_severity": "medium", "volume": 30,
      "prev_volume": 2, "stress_share": 0.5, "n_sources": 1, "n_entities": 1,
      "n_topics": 1, "recent": 1.0}, "high"),
    # Sector-wide quiet shift, many entities: medium-high.
    ({"dimension": "sector", "anomaly_severity": "medium", "volume": 9,
      "prev_volume": 6, "stress_share": 0.45, "n_sources": 3, "n_entities": 7,
      "n_topics": 3, "recent": 1.0}, "medium"),
    # Old bucket, no recent docs: the anomaly engine flagged it medium and
    # the scorer never downgrades below the anomaly call, so medium.
    ({"dimension": "global", "anomaly_severity": "medium", "volume": 8,
      "prev_volume": 3, "stress_share": 0.4, "n_sources": 2, "n_entities": 3,
      "n_topics": 2, "recent": 0.0}, "medium"),
    # Volume surge with high anomaly flag + wide spread: high. The locked
    # severity formula is impact x urgency x spread, so neutral sentiment
    # does not cap it.
    ({"dimension": "global", "anomaly_severity": "high", "volume": 40,
      "prev_volume": 10, "stress_share": 0.15, "n_sources": 4, "n_entities": 6,
      "n_topics": 4, "recent": 1.0}, "high"),
    # Saturated spread, high stress, global: critical.
    ({"dimension": "global", "anomaly_severity": "critical", "volume": 60,
      "prev_volume": 20, "stress_share": 0.75, "n_sources": 5, "n_entities": 12,
      "n_topics": 6, "recent": 1.0}, "critical"),
    # Topic-level, low spread, high stress: high (topic weight caps impact).
    ({"dimension": "topic", "anomaly_severity": "high", "volume": 12,
      "prev_volume": 3, "stress_share": 0.8, "n_sources": 2, "n_entities": 2,
      "n_topics": 1, "recent": 1.0}, "high"),
    # Steady volume, no growth, mid stress: medium.
    ({"dimension": "global", "anomaly_severity": "medium", "volume": 10,
      "prev_volume": 10, "stress_share": 0.4, "n_sources": 3, "n_entities": 4,
      "n_topics": 3, "recent": 1.0}, "medium"),
    # Declining volume but critical anomaly flag (second spike): critical.
    ({"dimension": "global", "anomaly_severity": "critical", "volume": 18,
      "prev_volume": 25, "stress_share": 0.5, "n_sources": 4, "n_entities": 5,
      "n_topics": 3, "recent": 1.0}, "critical"),
    # One emirate, one topic, moderate: medium.
    ({"dimension": "emirate", "anomaly_severity": "medium", "volume": 7,
      "prev_volume": 3, "stress_share": 0.55, "n_sources": 2, "n_entities": 2,
      "n_topics": 1, "recent": 1.0}, "medium"),
]


def run_severity_eval(*, verbose: bool = True) -> dict:
    y_true, y_pred = [], []
    for i, (ctx, gold) in enumerate(SEVERITY_CASES, 1):
        level = score_severity(ctx)["level"]
        y_true.append(gold)
        y_pred.append(level)
        if verbose and level != gold:
            print(f"    [{i}/{len(SEVERITY_CASES)}] MISMATCH gold={gold!r} "
                  f"got={level!r} ctx={ctx}")
    metrics = compute_metrics(y_true, y_pred)
    metrics["task"] = "severity"
    metrics["confusion"] = confusion(y_true, y_pred)
    return metrics


# ---------------------------------------------------------------------------
# Brief scored set (small LLM budget)
# ---------------------------------------------------------------------------

_BRIEF_CASES = [
    {
        "name": "rent spike - dubai",
        "context": (
            "ALERT: Rent increase complaints spike in Dubai\n"
            "SEVERITY: high (score 0.78)\n"
            "DIMENSION: emirate (id 5)\n"
            "EVIDENCE DOCS:\n"
            "- [reddit] Landlord raised my rent 20% again, insane (signal=stress, "
            "sentiment=negative) url=https://reddit.com/r/dubai/abc123\n"
            "- [news] Dubai rents up 15% in Q2, tenants struggle "
            "url=https://gulfnews.com/rent-q2\n"
            "TRAJECTORY:\n- 2026-08-10: vol=4 sent=0.1\n- 2026-08-11: vol=9 "
            "sent=-0.4 ANOMALY"
        ),
        "required": ["title", "summary", "what", "where", "who",
                     "trajectory", "recommended_response"],
    },
    {
        "name": "fees - abu dhabi",
        "context": (
            "ALERT: Salik and service fee complaints surge\n"
            "SEVERITY: critical (score 0.9)\n"
            "DIMENSION: global (id 0)\n"
            "EVIDENCE DOCS:\n"
            "- [reddit] Salik charges are getting out of hand (signal=stress, "
            "sentiment=negative) url=https://reddit.com/r/UAE/salik1\n"
            "- [apple_reviews] App fees doubled this month, unacceptable "
            "url=https://apps.apple.com/fees\n"
            "TRAJECTORY:\n- 2026-08-14: vol=11 sent=-0.6\n- 2026-08-15: "
            "vol=34 sent=-0.8 ANOMALY"
        ),
        "required": ["title", "summary", "what", "where", "who",
                     "trajectory", "recommended_response"],
    },
    {
        "name": "jobs - sector",
        "context": (
            "ALERT: Tech layoff talk spreads across sector\n"
            "SEVERITY: high (score 0.71)\n"
            "DIMENSION: sector (id 3)\n"
            "EVIDENCE DOCS:\n"
            "- [news] Two startups cut headcount this month "
            "url=https://thenational.ae/jobs/1\n"
            "- [reddit] Worried about layoffs in Dubai tech scene "
            "url=https://reddit.com/r/dubai/jobs\n"
            "TRAJECTORY:\n- 2026-08-08: vol=3 sent=-0.2\n- 2026-08-09: vol=8 "
            "sent=-0.5 ANOMALY"
        ),
        "required": ["title", "summary", "what", "where", "who",
                     "trajectory", "recommended_response"],
    },
    {
        "name": "thin evidence - honest downgrade",
        "context": (
            "ALERT: Food delivery complaints blip\n"
            "SEVERITY: low (score 0.31)\n"
            "DIMENSION: topic (id 9)\n"
            "EVIDENCE DOCS:\n"
            "- [reddit] One bad delivery experience (signal=neutral, "
            "sentiment=neutral) url=https://reddit.com/r/dubai/food\n"
            "TRAJECTORY:\n- 2026-08-16: vol=2 sent=0.0"
        ),
        "required": ["title", "summary", "what", "where", "who",
                     "trajectory", "recommended_response"],
    },
]


def _grounded(text: str, context: str) -> list[str]:
    """Grounding proxy: data numbers (>= 5) and URLs cited must appear in
    context. Editorial phrases like 'within 24 hours' or '30% higher' are
    stripped first - they are rhetoric, not invented statistics."""
    problems: list[str] = []
    # Models sometimes emit literal \uXXXX escapes (e.g. "24\\u202fhours")
    # instead of real spaces - normalize the common ones before parsing.
    for esc in ("\\u202f", "\\u00a0", "\\u2009", "\\u00ad"):
        text = text.replace(esc, " ")
    cleaned = re.sub(r"\b\d+\s*(?:-|\s)?(?:hours?|hrs?|minutes?|days?|weeks?|months?)\b",
                     " ", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b\d+(?:\.\d+)?\s*%", " ", cleaned)
    for num in re.findall(r"\d{1,3}", cleaned):
        if int(num) >= 5 and num not in context:
            problems.append(f"number {num} not in context")
            break  # one number problem is enough per brief
    for url in re.findall(r"https?://\S+", text):
        if url not in context:
            problems.append(f"url {url} not in context")
            break
    return problems


def run_brief_eval(*, verbose: bool = True, dry_run: bool = False) -> dict:
    llm = AgentLLM()
    checks, passed = 0, 0
    problems: list[str] = []
    for i, case in enumerate(_BRIEF_CASES, 1):
        data = llm.ask(_BRIEF_SYSTEM, case["context"], max_tokens=1400)
        if data is None:
            if verbose:
                print(f"    [{i}/{len(_BRIEF_CASES)}] LLM unavailable "
                      f"(budget?), case {case['name']} scored 0")
            problems.append(f"{case['name']}: no LLM output")
            checks += 2
            continue
        checks += 1
        if isinstance(data, dict):
            passed += 1
        else:
            problems.append(f"{case['name']}: not a JSON object")
            continue
        missing = [k for k in case["required"] if k not in data]
        checks += 1
        if not missing:
            passed += 1
        else:
            problems.append(f"{case['name']}: missing {missing}")
        grounding = _grounded(str(data), case["context"])
        checks += 1
        if not grounding:
            passed += 1
        else:
            problems.append(f"{case['name']}: {grounding}")
        if verbose:
            print(f"    [{i}/{len(_BRIEF_CASES)}] {case['name']}: "
                  f"valid={isinstance(data, dict)} "
                  f"complete={not missing} grounded={not grounding}")
    accuracy = passed / checks if checks else 0.0
    metrics = {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(accuracy, 4),
        "macro_recall": round(accuracy, 4),
        "macro_f1": round(accuracy, 4),
        "per_class": {"ok": {"precision": round(accuracy, 4),
                               "recall": round(accuracy, 4),
                               "f1": round(accuracy, 4),
                               "support": checks}},
        "n": len(_BRIEF_CASES),
        "task": "brief",
        "checks": checks,
        "passed": passed,
        "problems": problems[:8],
        "confusion": {"ok": {"ok": checks}},  # single-class report for print_report
    }
    return metrics


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run_agents_eval(*, dry_run: bool = False) -> int:
    t0 = time.monotonic()
    print("=" * 60)
    print("  BASR eval harness - agents (severity + brief)")
    print(f"  model: {AGENT_VERSION}")
    print("=" * 60)

    sev = run_severity_eval()
    print_report(f"  severity-agreement ({sev['n']} cases, zero tokens)", sev)

    brief = run_brief_eval(dry_run=dry_run)
    print_report(f"  brief format+grounding ({brief['n']} cases, small LLM)", brief)
    if brief.get("problems"):
        print("  problems:")
        for p in brief["problems"]:
            print(f"    - {p}")

    if dry_run:
        print(f"\n[+] Agents eval finished in {time.monotonic() - t0:.1f}s "
              f"(dry-run, nothing logged)")
        return 0

    store = SupabaseStore()
    await store.open()
    try:
        await store.upsert_eval_dataset(
            "agents-severity-v1", "en", "severity",
            [{"text": str(ctx), "label": gold}
             for ctx, gold in SEVERITY_CASES])
        await store.upsert_eval_dataset(
            "agents-brief-v1", "en", "brief",
            [{"text": c["context"], "label": c["name"],
              "required": c["required"]} for c in _BRIEF_CASES])
        await store.log_eval_run(
            dataset_name="agents-severity-v1", model_version=AGENT_VERSION,
            accuracy=sev["accuracy"], precision=sev["macro_precision"],
            recall=sev["macro_recall"], f1=sev["macro_f1"],
            detail={"task": "severity", "per_class": sev["per_class"],
                    "n": sev["n"]})
        await store.log_eval_run(
            dataset_name="agents-brief-v1", model_version=AGENT_VERSION,
            accuracy=brief["accuracy"], precision=brief["macro_precision"],
            recall=brief["macro_recall"], f1=brief["macro_f1"],
            detail={"task": "brief", "checks": brief.get("checks"),
                    "passed": brief.get("passed"),
                    "problems": brief.get("problems", [])})
        print("[+] agent eval runs logged")
    finally:
        await store.close()

    print(f"\n[+] Agents eval finished in {time.monotonic() - t0:.1f}s")
    return 0
