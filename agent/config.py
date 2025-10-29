"""Central configuration for paths, thresholds, and numeric limits."""

from __future__ import annotations

import sys
from pathlib import Path


def _detect_project_root() -> Path:
    """Return the project root whether running from source or a frozen bundle."""
    if getattr(sys, "frozen", False):
        # When packaged with PyInstaller, use the folder that hosts the executable.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


PROJECT_ROOT = _detect_project_root()
CSV_PATH = PROJECT_ROOT / "system_report.csv"
BUFFER_PATH = PROJECT_ROOT / "system_report.buffer"
ALERT_LOG_PATH = PROJECT_ROOT / "alerts.log"
REPORT_PATH = PROJECT_ROOT / "report.html"

CSV_FIELDS = [
    "timestamp",
    "cpu_percent",
    "memory_percent",
    "memory_used",
    "memory_total",
    "disk_percent",
    "disk_used",
    "disk_total",
    "net_bytes_sent",
    "net_bytes_recv",
    "uptime_seconds",
]

ALERT_THRESHOLDS = {
    "cpu_percent": 90.0,
    "memory_percent": 85.0,
    "disk_percent": 90.0,
}

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
