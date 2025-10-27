"""Persistent logging for threshold alerts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from agent import config


def log_alerts(alerts: List[str], log_path: Path | None = None) -> None:
    """Persist alerts to the alert log with timestamps."""
    target = Path(log_path) if log_path else config.ALERT_LOG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with target.open("a") as log_file:
        for alert in alerts:
            log_file.write(f"{timestamp} - {alert}\n")
