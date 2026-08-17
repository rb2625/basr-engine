"""Deterministic fallback tests (the budget-wall behavior must stay honest)
plus eval metrics math."""

from basr.agents.brief import _fallback_brief
from basr.agents.reports import _fallback_narrative
from basr.eval.harness import compute_metrics


def _stats(**over):
    base = {
        "period_days": 1,
        "current_volume": 10,
        "prior_volume": 85,
        "volume_delta_pct": -88.2,
        "sentiment_avg": None,
        "sentiment_prior": -0.153,
        "anomaly_flags": 0,
        "open_alerts": 4,
        "top_topics": [{"topic": "Rent and housing", "volume": 5}],
        "top_sectors": [],
        "top_emirates": [{"emirate": "dubai", "volume": 10}],
    }
    base.update(over)
    return base


def test_fallback_narrative_is_grounded():
    n = _fallback_narrative(_stats())
    assert "10" in n["narrative"]          # current volume
    assert "down" in n["narrative"]        # -88.2% reads as down
    assert "4" in n["narrative"]           # open alerts
    assert any("-88%" in h for h in n["headlines"])
    assert any("Rent and housing" in h for h in n["headlines"])


def test_fallback_narrative_handles_missing_sentiment():
    n = _fallback_narrative(_stats())
    assert "n/a" in n["narrative"]         # sentiment_avg None is honest


def test_fallback_brief_has_all_required_fields():
    alert = {"id": 1, "title": "UAE signal surge", "severity": "critical"}
    bucket = {"dimension_type": "global", "dimension_id": 0,
              "granularity": "day", "volume": 12}
    sev = {"level": "critical", "score": 0.8,
           "factors": {"volume": 12, "stress_share": 0.5,
                        "dimension": "global"}}
    brief = _fallback_brief(alert, bucket, [], sev, [])
    for key in ("title", "summary", "what", "where", "who",
                "trajectory", "recommended_response"):
        assert key in brief
    assert brief["recommended_response"][0]["action"]
    assert brief["recommended_response"][0]["owner"]
    assert brief["recommended_response"][0]["rationale"]


def test_compute_metrics_exact():
    m = compute_metrics(["a", "a", "b"], ["a", "b", "b"])
    assert m["accuracy"] == 0.6667
    # The harness defines macro-F1 as F1(macro-P, macro-R), i.e. 0.75 here.
    assert m["macro_f1"] == 0.75
    assert m["n"] == 3
