"""Unit tests for threshold validation."""

from agent.validation import check_thresholds


def test_thresholds_trigger_alerts() -> None:
    stats = {"cpu_percent": 95.0, "memory_percent": 50.0, "disk_percent": 91.0}
    alerts = check_thresholds(stats)
    assert "cpu_percent at 95.0% exceeds 90.0%" in alerts
    assert "disk_percent at 91.0% exceeds 90.0%" in alerts
    assert not any("memory_percent" in alert for alert in alerts)


def test_thresholds_no_alerts_when_below_limits() -> None:
    stats = {"cpu_percent": 10.0, "memory_percent": 10.0, "disk_percent": 10.0}
    alerts = check_thresholds(stats)
    assert alerts == []
