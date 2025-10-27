"""
Local system health monitor utilities.
"""

from __future__ import annotations

import csv
import json
import os
import smtplib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List

import psutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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


def send_email(alerts: List[str], stats: Dict[str, object], sender: str | None = None, recipient: str | None = None) -> bool:
    """Send an alert email through Gmail SMTP using env configured credentials."""
    sender_email = sender or os.getenv("SENDER_EMAIL")
    password = os.getenv("APP_PASSWORD")
    recipient_email = recipient or os.getenv("RECIPIENT_EMAIL")

    if not sender_email or not password or not recipient_email:
        print("Email credentials missing; skipping email alert.")
        return False

    subject = "System health alert"
    lines = ["The following thresholds were exceeded:"] + [f" - {alert}" for alert in alerts]
    lines.append("\nKey metrics snapshot:")
    for key in ("cpu_percent", "memory_percent", "disk_percent", "uptime_seconds"):
        lines.append(f" * {key}: {stats.get(key)}")
    body = "\n".join(lines)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
        return True
    except smtplib.SMTPException as exc:
        print(f"Failed to send email alerts: {exc}")
        return False


def update_html_report(stats: Dict[str, object], alerts: List[str], report_path: Path | None = None) -> Path:
    """Generate a minimal HTML dashboard for the latest stats."""
    target = Path(report_path) if report_path else REPORT_PATH
    top_processes = stats.get("top_processes", [])
    process_rows = "\n".join(
        f"<tr><td>{proc.get('pid')}</td><td>{proc.get('name')}</td><td>{proc.get('cpu_percent')}</td><td>{proc.get('memory_percent')}</td></tr>"
        for proc in top_processes
    ) or "<tr><td colspan='4'>No process data</td></tr>"

    alert_items = "".join(f"<li>{alert}</li>" for alert in alerts) or "<li>No active alerts</li>"
    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>System Health Report</title>
<style>
 body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f4f6f8; }}
 .card {{ background: #fff; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); margin-bottom: 1.5rem; }}
 table {{ width: 100%; border-collapse: collapse; }}
 th, td {{ text-align: left; padding: 0.5rem; border-bottom: 1px solid #e1e5eb; }}
 th {{ background: #f0f3f7; }}
 .metrics {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
 .metric {{ flex: 1 1 200px; background: #eef2f7; padding: 1rem; border-radius: 6px; }}
</style>
</head>
<body>
<div class=\"card\">
  <h1>System Health Report</h1>
  <p>Generated at {stats.get('timestamp')}</p>
  <div class=\"metrics\">
    <div class=\"metric\"><strong>CPU</strong><br>{stats.get('cpu_percent')}%</div>
    <div class=\"metric\"><strong>Memory</strong><br>{stats.get('memory_percent')}%</div>
    <div class=\"metric\"><strong>Disk</strong><br>{stats.get('disk_percent')}%</div>
    <div class=\"metric\"><strong>Uptime</strong><br>{stats.get('uptime_seconds')}s</div>
  </div>
</div>
<div class=\"card\">
  <h2>Active Alerts</h2>
  <ul>{alert_items}</ul>
</div>
<div class=\"card\">
  <h2>Top Processes</h2>
  <table>
    <thead><tr><th>PID</th><th>Name</th><th>CPU%</th><th>Mem%</th></tr></thead>
    <tbody>
      {process_rows}
    </tbody>
  </table>
</div>
</body>
</html>
"""
    target.write_text(html)
    return target


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
        if send_email(alerts, stats):
            print("Email alerts dispatched via Gmail SMTP.")
        else:
            print("Email alerts skipped or failed.")
    else:
        print("No threshold alerts detected.")

    report_path = update_html_report(stats, alerts)
    print(f"Updated HTML report at {report_path}")


if __name__ == "__main__":
    main()
