"""Phase 4 - early warning: time-series aggregation, anomaly detection, alerts.

- ``aggregate`` builds the ``time_series`` table (five dimensions)
- ``anomaly`` flags volume spikes (z-score + STL ensemble) and creates alerts
- ``alerts`` delivers alerts over Telegram/Resend and manages the lifecycle

Zero LLM tokens: this layer is pure statistics over the derived tables.
"""

from .aggregate import build_time_series
from .anomaly import detect_anomalies, severity_for
from .alerts import deliver_alerts

__all__ = ["build_time_series", "detect_anomalies", "severity_for", "deliver_alerts"]
