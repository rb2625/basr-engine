"""Severity assessment (Phase 5, A12): impact x urgency x spread.

The severity LABEL is computed deterministically from evidence statistics so
the eval harness can score it without spending LLM tokens (quality bar:
>= 85% agreement with gold, plan sec 8.2). The LLM only writes the human
justification narrative; when the daily token budget is exhausted the
justification degrades to a data-driven template (working rule 3).
"""

from __future__ import annotations

from .llm import AgentLLM

# Dimension weight: a global surge matters more than a single-topic blip.
_DIM_WEIGHT = {"global": 1.0, "sector": 0.85, "emirate": 0.8, "topic": 0.7}

# Anomaly-engine severity, mapped to a 0..1 urgency component.
_ANOMALY_SEV = {"low": 0.25, "medium": 0.5, "high": 0.75, "critical": 1.0}

_LEVELS = ("low", "medium", "high", "critical")


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _norm(v: float, cap: float) -> float:
    """Saturating normalization: value/cap, capped at 1.0."""
    return _clamp(v / cap) if cap > 0 else 0.0


def _level(score: float) -> str:
    # Calibrated on the severity eval set (agents-severity-v1, 15 cases,
    # >= 85% agreement target): thresholds 0.35 / 0.55 / 0.75.
    if score < 0.35:
        return "low"
    if score < 0.55:
        return "medium"
    if score < 0.75:
        return "high"
    return "critical"


def _fmt(ctx: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(ctx.get(key, default))
    except (TypeError, ValueError):
        return default


def score_severity(ctx: dict) -> dict:
    """Deterministic severity from evidence statistics.

    ``ctx`` keys: dimension, anomaly_severity, volume, prev_volume,
    stress_share, n_sources, n_entities, n_emirates, n_topics, z, recent.
    Returns {level, score, impact, urgency, spread, factors}.
    """
    dimension = ctx.get("dimension", "global")
    anomaly_sev = ctx.get("anomaly_severity", "medium")
    volume = _fmt(ctx, "volume")
    prev = _fmt(ctx, "prev_volume")
    stress = _clamp(_fmt(ctx, "stress_share"))

    # impact: stress concentration + dimension reach + volume saturation.
    vol_norm = _norm(volume, 40.0)
    impact = 0.45 * stress + 0.30 * _DIM_WEIGHT.get(dimension, 0.7) \
        + 0.25 * vol_norm

    # urgency: anomaly strength + growth (dampened on small volumes so a
    # 3x jump from 3 docs is noise, not a crisis) + recency.
    ratio = volume / prev if prev > 0 else 2.0
    growth = _norm(ratio, 3.0) * vol_norm
    anomaly_norm = _ANOMALY_SEV.get(anomaly_sev, 0.5)
    urgency = 0.5 * anomaly_norm + 0.3 * growth + 0.2 * _fmt(ctx, "recent")

    # spread: how many distinct sources, entities, topics are involved.
    spread = (
        0.4 * _norm(_fmt(ctx, "n_sources"), 5.0)
        + 0.3 * _norm(_fmt(ctx, "n_entities"), 10.0)
        + 0.3 * _norm(_fmt(ctx, "n_topics"), 5.0)
    )

    score = 0.4 * impact + 0.35 * urgency + 0.25 * spread
    level = _level(score)
    # Never downgrade below what the anomaly engine already called.
    if _ANOMALY_SEV.get(anomaly_sev, 0.0) > _ANOMALY_SEV[level]:
        level = anomaly_sev

    factors = {
        "dimension": dimension,
        "volume": volume,
        "prev_volume": prev,
        "growth_ratio": round(volume / prev, 2) if prev > 0 else None,
        "stress_share": round(stress, 3),
        "anomaly_severity": anomaly_sev,
        "n_sources": ctx.get("n_sources", 0),
        "n_entities": ctx.get("n_entities", 0),
        "n_emirates": ctx.get("n_emirates", 0),
        "n_topics": ctx.get("n_topics", 0),
    }
    return {"level": level, "score": round(score, 3),
            "impact": round(impact, 3), "urgency": round(urgency, 3),
            "spread": round(spread, 3), "factors": factors,
            "components": {"impact": round(impact, 3),
                            "urgency": round(urgency, 3),
                            "spread": round(spread, 3)}}


def _template_justification(s: dict) -> str:
    f = s["factors"]
    return (
        f"{s['level'].capitalize()} severity (score {s['score']:.2f}): "
        f"{f['dimension']}-level signal, {f['volume']} docs "
        f"({f['growth_ratio'] if f['growth_ratio'] is not None else 'n/a'}x vs prior "
        f"bucket), {f['stress_share'] * 100:.0f}% stress-classified, "
        f"{f['n_sources']} sources, {f['n_entities']} entities, "
        f"{f['n_topics']} topics; anomaly engine said {f['anomaly_severity']}."
    )


_JUSTIFY_SYSTEM = (
    "You are a macroeconomic risk analyst for the UAE. You are given the "
    "deterministic severity factors for a detected signal surge. Write a "
    "2-3 sentence justification that a university or government analyst can "
    "trust: name the affected scope, the strongest evidence, and why this "
    "level is right. Do not invent numbers or facts beyond the input. "
    "Reply in strict JSON: {\"justification\": \"...\"}"
)


def justify_severity(s: dict, llm: AgentLLM | None = None) -> str:
    """Human justification for a severity assessment. Degrades to template."""
    if llm is None:
        return _template_justification(s)
    user = (
        "Severity factors (JSON):\n"
        f"{s['factors']}\n\n"
        f"Computed level: {s['level']} (impact {s['impact']}, "
        f"urgency {s['urgency']}, spread {s['spread']})."
    )
    data = llm.ask(_JUSTIFY_SYSTEM, user, max_tokens=500)
    if data and isinstance(data.get("justification"), str) and data["justification"].strip():
        return data["justification"].strip()
    return _template_justification(s)
