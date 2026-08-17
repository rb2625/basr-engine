"""Severity scorer unit tests (Phase 5, A13). The 15-case eval set covers
agreement; these lock in the specific rules: the anomaly floor, growth
dampening on small volumes, and the level boundaries."""

from basr.agents.severity import score_severity


def _ctx(**over):
    base = {
        "dimension": "global",
        "anomaly_severity": "medium",
        "volume": 10,
        "prev_volume": 10,
        "stress_share": 0.4,
        "n_sources": 3,
        "n_entities": 4,
        "n_topics": 3,
        "recent": 1.0,
    }
    base.update(over)
    return base


def test_anomaly_floor_never_downgrades():
    # A critical anomaly call must survive even thin evidence.
    r = score_severity(_ctx(anomaly_severity="critical", volume=5,
                            prev_volume=4, stress_share=0.4, n_sources=1,
                            n_entities=1, n_topics=1))
    assert r["level"] == "critical"


def test_large_global_stress_surge_is_critical():
    r = score_severity(_ctx(anomaly_severity="critical", volume=75,
                            prev_volume=12, stress_share=0.6, n_sources=4,
                            n_entities=8, n_topics=5))
    assert r["level"] == "critical"


def test_small_blip_is_low():
    r = score_severity(_ctx(anomaly_severity="low", volume=3, prev_volume=1,
                            stress_share=0.2, n_sources=1, n_entities=1,
                            n_topics=1))
    assert r["level"] == "low"


def test_steady_volume_is_medium():
    r = score_severity(_ctx(anomaly_severity="medium", volume=10,
                            prev_volume=10, stress_share=0.4))
    assert r["level"] == "medium"


def test_growth_dampened_on_tiny_volume():
    # 3x growth from 3 docs is noise; the same 3x from 60 docs is a surge.
    # The scorer must order them correctly (scores, not just levels).
    small = score_severity(_ctx(anomaly_severity="low", volume=3,
                                prev_volume=1, stress_share=0.2,
                                n_sources=1, n_entities=1, n_topics=1))
    big = score_severity(_ctx(anomaly_severity="low", volume=60,
                              prev_volume=20, stress_share=0.2,
                              n_sources=1, n_entities=1, n_topics=1))
    assert small["level"] in ("low", "medium")
    assert big["score"] > small["score"]
    assert big["level"] in ("medium", "high", "critical")


def test_factors_and_components_present():
    r = score_severity(_ctx())
    assert set(r) >= {"level", "score", "impact", "urgency", "spread",
                      "factors", "components"}
    assert 0.0 <= r["score"] <= 1.0
    assert r["factors"]["dimension"] == "global"
