"""HTML reporting utilities."""

from __future__ import annotations

from pathlib import Path
from typing import List

from agent import config
from agent.dto import SystemSnapshot


def update_html_report(
    stats: SystemSnapshot,
    alerts: List[str],
    report_path: Path | None = None,
) -> Path:
    """Generate a minimal HTML dashboard for the latest stats."""
    target = Path(report_path) if report_path else config.REPORT_PATH
    top_processes = stats.get("top_processes", [])
    process_rows = "\n".join(
        f"<tr><td>{proc.get('pid')}</td><td>{proc.get('name')}</td>"
        f"<td>{proc.get('cpu_percent')}</td><td>{proc.get('memory_percent')}</td></tr>"
        for proc in top_processes
    ) or "<tr><td colspan='4'>No process data</td></tr>"

    alert_items = "".join(f"<li>{alert}</li>" for alert in alerts) or "<li>No active alerts</li>"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
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
<div class="card">
  <h1>System Health Report</h1>
  <p>Generated at {stats.get('timestamp')}</p>
  <div class="metrics">
    <div class="metric"><strong>CPU</strong><br>{stats.get('cpu_percent')}%</div>
    <div class="metric"><strong>Memory</strong><br>{stats.get('memory_percent')}%</div>
    <div class="metric"><strong>Disk</strong><br>{stats.get('disk_percent')}%</div>
    <div class="metric"><strong>Uptime</strong><br>{stats.get('uptime_seconds')}s</div>
  </div>
</div>
<div class="card">
  <h2>Active Alerts</h2>
  <ul>{alert_items}</ul>
</div>
<div class="card">
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
