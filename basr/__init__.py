"""
BASR Intelligence Engine - UAE public sentiment intelligence and decision support.

BASR (بصر, "insight") continuously ingests public discourse about the UAE across
Reddit, news, YouTube, reviews, and live feeds - in Arabic, Arabizi, and English -
classifies signals, detects emerging issues, and produces decision-ready briefings.

This package is the foundation of the v2 platform. Modules:

    adapters/       pluggable source adapters (one schema in, swappable sources out)
    nlp/            normalization, classification, sentiment, topics, entities
    store/          persistence (Supabase) and schema
    intelligence/   time series, anomaly detection, decision briefs
    report/         client-facing deliverables (PDF, ...)
"""

__version__ = "2.0.0"
