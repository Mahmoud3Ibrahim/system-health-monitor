"""System metrics collector built on psutil."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import List

import psutil

from agent.dto import ProcessSnapshot, SystemSnapshot


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


def get_system_stats(top_n: int = 5) -> SystemSnapshot:
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
