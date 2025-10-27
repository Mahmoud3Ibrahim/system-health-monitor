"""High-level orchestration for collecting, persisting, and alerting."""

from __future__ import annotations

from typing import List

from agent import config
from agent.business.system_collector import get_system_stats
from agent.dto import SystemSnapshot
from agent.io.alert_logger import log_alerts
from agent.io.csv_sink import save_csv
from agent.io.email_client import send_email
from agent.io.html_report import update_html_report
from agent.validation.thresholds import check_thresholds


class MonitorService:
    """Coordinates the monitoring workflow."""

    def __init__(self) -> None:
        self.csv_path = config.CSV_PATH
        self.buffer_path = config.BUFFER_PATH
        self.alert_log_path = config.ALERT_LOG_PATH
        self.report_path = config.REPORT_PATH

    def run_once(self) -> SystemSnapshot:
        """Collect stats, persist outputs, dispatch alerts, and render HTML."""
        stats = get_system_stats()
        self._print_stats(stats)

        if save_csv(stats, self.csv_path, self.buffer_path):
            print(f"Saved metrics to {self.csv_path}")
        else:
            print(f"Write failed; buffered data at {self.buffer_path}")

        alerts = check_thresholds(stats)
        self._handle_alerts(alerts, stats)

        report_path = update_html_report(stats, alerts, self.report_path)
        print(f"Updated HTML report at {report_path}")
        self._print_run_guidance()
        return stats

    def _print_stats(self, stats: SystemSnapshot) -> None:
        print("Current system snapshot:")
        for key, value in stats.items():
            if key == "top_processes":
                print(f"{key}: {len(value)} entries")
            else:
                print(f"{key}: {value}")

    def _handle_alerts(self, alerts: List[str], stats: SystemSnapshot) -> None:
        if not alerts:
            print("No threshold alerts detected.")
            return

        print("Threshold alerts detected:")
        for alert in alerts:
            print(f" - {alert}")
        log_alerts(alerts, self.alert_log_path)
        print(f"Logged alerts to {self.alert_log_path}")

        if send_email(alerts, stats):
            print("Email alerts dispatched via Gmail SMTP.")
        else:
            print("Email alerts skipped or failed.")

    @staticmethod
    def _print_run_guidance() -> None:
        """Output local run, Gmail app password, and roadmap guidance."""
        print("\nRun locally:")
        print(" python -m agent.monitor")
        print(
            "Gmail App Password: https://myaccount.google.com/apppasswords "
            "-> Mail -> Custom name -> copy the 16-char token."
        )
        print("Recommended next steps: 1) Add Telegram alerts  2) Dockerize this monitor for portability.")
