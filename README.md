# System Health Monitor

A lightweight, production-ready agent that captures local system telemetry, persists it for historical review, and raises alerts through email.

## Features
- CPU, memory, disk, network, uptime, and top process sampling powered by `psutil`.
- Resilient CSV persistence with buffering during transient disk issues.
- Threshold-based alerting (CPU > 90%, Memory > 85%, Disk > 90%) with console logging, `alerts.log`, and Gmail SMTP notifications.
- Auto-generated HTML snapshot (`report.html`) plus scriptable sample capture for docs/screenshots.
- Modular code ready for cron/systemd scheduling, container builds, or external alert transports.

## Architecture Overview
- `agent/dto`: dataclasses and typed dicts for telemetry.
- `agent/business`: psutil collectors plus the MonitorService orchestrator.
- `agent/io`: CSV writer, HTML renderer, alert logger, and SMTP client.
- `agent/validation`: threshold policies (extensible for future rules).
- `tests`: pytest suite ready for additional unit/contract cases.

## Requirements
- Python 3.10+
- `psutil` (install via `pip install -r requirements.txt`)
- Gmail account with App Password enabled for SMTP relay

## Getting Started
1. **Clone & install**
   ```bash
   git clone <repo-url>
   cd system-health-monitor
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/macOS
   pip install -r requirements.txt
   ```
2. **Configure environment variables** (shell, `.env`, or scheduler)
   ```bash
   set SENDER_EMAIL="you@gmail.com"
   set RECIPIENT_EMAIL="ops-team@example.com"
   set APP_PASSWORD="your-16-char-app-password"
   ```
3. **Run the monitor manually**
   ```bash
   python -m agent.monitor
   ```

## Gmail App Password Setup
1. Enable 2-Step Verification on your Google account.
2. Visit https://myaccount.google.com/apppasswords.
3. Choose "Mail" as the app and "Other (Custom)" for the device (e.g., "System Monitor").
4. Generate and copy the 16-character password; store it as `APP_PASSWORD`.
5. Keep the password secret—revoke it immediately if exposed.

## Scheduling Options
- **Cron (Linux/macOS)**: run every 5 minutes
  ```cron
  */5 * * * * /usr/bin/python3 /opt/system-health-monitor/agent/monitor.py >> /var/log/system-monitor.log 2>&1
  ```
- **systemd service**: create `/etc/systemd/system/system-health-monitor.service`
  ```ini
  [Unit]
  Description=System Health Monitor
  After=network.target

  [Service]
  Type=simple
  Environment=SENDER_EMAIL=you@gmail.com
  Environment=RECIPIENT_EMAIL=ops-team@example.com
  Environment=APP_PASSWORD=xxxxxxxxxxxxxxxx
  WorkingDirectory=/opt/system-health-monitor
  ExecStart=/usr/bin/python3 -m agent.monitor
  Restart=on-failure

  [Install]
  WantedBy=multi-user.target
  ```
  Then run `sudo systemctl daemon-reload && sudo systemctl enable --now system-health-monitor`.

## HTML Reports & Screenshots
- `agent.monitor.update_html_report()` writes `report.html` each run.
- `scripts/generate_sample_html.py` fabricates sample data for documentation or screenshot capture.

## Security Notes
- Never commit real credentials—use environment variables or secret managers.
- Rotate Gmail App Passwords periodically.
- Limit filesystem permissions on logs and CSVs if they contain sensitive process names.

## Recommended Next Steps
1. Add Telegram or Slack webhook alerts for on-call redundancy.
2. Package the agent into a Docker image with a minimal base and baked-in scheduler.
3. Stream metrics to a TSDB (InfluxDB/Prometheus) for long-term trending.


