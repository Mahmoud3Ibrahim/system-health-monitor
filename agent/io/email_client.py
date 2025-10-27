"""Gmail SMTP client for alert notifications."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import List

from agent import config
from agent.dto import SystemSnapshot


def send_email(
    alerts: List[str],
    stats: SystemSnapshot,
    sender: str | None = None,
    recipient: str | None = None,
) -> bool:
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
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
        return True
    except smtplib.SMTPException as exc:
        print(f"Failed to send email alerts: {exc}")
        return False
