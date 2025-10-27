"""
Local system health monitor utilities.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import psutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "system_report.csv"
BUFFER_PATH = PROJECT_ROOT / "system_report.buffer"
ALERT_LOG_PATH = PROJECT_ROOT / "alerts.log"
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


@dataclass
class ProcessSnapshot:
    """Lightweight view of a running process."""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


def _collect_top_processes(limit: int = 5) -> List[ProcessSnapshot]:
    """Return the top processes sorted by CPU usage."""
    snapshots: List[ProcessSnapshot] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            snapshots.append(
                ProcessSnapshot(
                    pid=info.get("pid", 0),
                    name=info.get("name") or "unknown",
                    cpu_percent=float(info.get("cpu_percent") or 0.0),
                    memory_percent=float(info.get("memory_percent") or 0.0),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    snapshots.sort(key=lambda proc: proc.cpu_percent, reverse=True)
    return snapshots[:limit]


def get_system_stats(top_n: int = 5) -> Dict[str, object]:
    """Gather CPU, memory, disk, network, uptime, and process telemetry."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    uptime_seconds = int(datetime.now(timezone.utc).timestamp() - psutil.boot_time())
    top_processes = [asdict(proc) for proc in _collect_top_processes(limit=top_n)]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_used": memory.used,
        "memory_total": memory.total,
        "disk_percent": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "net_bytes_sent": net.bytes_sent,
        "net_bytes_recv": net.bytes_recv,
        "uptime_seconds": uptime_seconds,
        "top_processes": top_processes,
    }


def _write_csv_rows(csv_path: Path, rows: List[Dict[str, object]]) -> None:
    """Append rows to the CSV, writing the header when needed."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()
    with csv_path.open("a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})


def _load_buffer(buffer_path: Path) -> List[Dict[str, object]]:
    if not buffer_path.exists():
        return []
    with buffer_path.open() as buffer_file:
        return [json.loads(line) for line in buffer_file if line.strip()]


def _persist_buffer(buffer_path: Path, rows: List[Dict[str, object]]) -> None:
    buffer_path.parent.mkdir(parents=True, exist_ok=True)
    with buffer_path.open("w") as buffer_file:
        for row in rows:
            buffer_file.write(json.dumps(row) + "\n")


def save_csv(stats: Dict[str, object], csv_path: Path | None = None, buffer_path: Path | None = None) -> bool:
    """Save stats to CSV, buffering locally if the write fails."""
    csv_target = Path(csv_path) if csv_path else CSV_PATH
    buffer_target = Path(buffer_path) if buffer_path else BUFFER_PATH

    buffered_rows = _load_buffer(buffer_target)
    rows_to_write = buffered_rows + [stats]

    try:
        _write_csv_rows(csv_target, rows_to_write)
        if buffer_target.exists():
            buffer_target.unlink()
        return True
    except OSError:
        _persist_buffer(buffer_target, rows_to_write)
        return False


def check_thresholds(stats: Dict[str, object]) -> List[str]:
    """Return alert messages for metrics that breach defined thresholds."""
    alerts: List[str] = []
    for metric, limit in ALERT_THRESHOLDS.items():
        value = float(stats.get(metric, 0.0))
        if value > limit:
            alerts.append(f"{metric} at {value:.1f}% exceeds {limit:.1f}%")
    return alerts


def _log_alerts(alerts: List[str], log_path: Path = ALERT_LOG_PATH) -> None:
    """Persist alerts to the alert log with timestamps."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    with log_path.open("a") as log_file:
        for alert in alerts:
            log_file.write(f"{timestamp} - {alert}\n")


def main() -> None:
    stats = get_system_stats()
    print("Current system snapshot:")
    for key, value in stats.items():
        if key == "top_processes":
            print(f"{key}: {len(value)} entries")
        else:
            print(f"{key}: {value}")

    if save_csv(stats):
        print(f"Saved metrics to {CSV_PATH}")
    else:
        print(f"Write failed; buffered data at {BUFFER_PATH}")

    alerts = check_thresholds(stats)
    if alerts:
        print("Threshold alerts detected:")
        for alert in alerts:
            print(f" - {alert}")
        _log_alerts(alerts)
        print(f"Logged alerts to {ALERT_LOG_PATH}")
    else:
        print("No threshold alerts detected.")


if __name__ == "__main__":
    main()
