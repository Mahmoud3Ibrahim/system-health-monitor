"""Threshold-based validation rules."""

from __future__ import annotations

from typing import List

from agent import config
from agent.dto import SystemSnapshot


def check_thresholds(stats: SystemSnapshot) -> List[str]:
    """Return alert messages for metrics that breach defined thresholds."""
    alerts: List[str] = []
    for metric, limit in config.ALERT_THRESHOLDS.items():
        value = float(stats.get(metric, 0.0))
        if value > limit:
            alerts.append(f"{metric} at {value:.1f}% exceeds {limit:.1f}%")
    return alerts
