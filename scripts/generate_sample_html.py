"""Generate a sample HTML report for documentation screenshots."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.io.html_report import update_html_report  # noqa: E402


def build_sample_stats() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "timestamp": now,
        "cpu_percent": 42.5,
        "memory_percent": 63.2,
        "memory_used": 8_589_934_592,
        "memory_total": 16_000_000_000,
        "disk_percent": 71.4,
        "disk_used": 380_000_000_000,
        "disk_total": 512_000_000_000,
        "net_bytes_sent": 1_234_567_890,
        "net_bytes_recv": 2_345_678_901,
        "uptime_seconds": 86400,
        "top_processes": [
            {"pid": 1001, "name": "python.exe", "cpu_percent": 35.2, "memory_percent": 12.6},
            {"pid": 2268, "name": "code.exe", "cpu_percent": 18.4, "memory_percent": 6.3},
            {"pid": 4321, "name": "chrome.exe", "cpu_percent": 12.1, "memory_percent": 8.1},
        ],
    }


def main() -> None:
    stats = build_sample_stats()
    alerts = ["cpu_percent at 98.2% exceeds 90.0%", "disk_percent at 92.0% exceeds 90.0%"]
    report_path = update_html_report(stats, alerts)
    print(f"Sample report generated at {report_path}")


if __name__ == "__main__":
    main()
