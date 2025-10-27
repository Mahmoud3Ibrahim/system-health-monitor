"""CLI entry point for the system health monitor."""

from __future__ import annotations

from agent.business import MonitorService


def main() -> None:
    service = MonitorService()
    service.run_once()


if __name__ == "__main__":
    main()
