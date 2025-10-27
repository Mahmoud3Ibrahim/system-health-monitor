"""Domain transfer objects representing collected telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, TypedDict


@dataclass
class ProcessSnapshot:
    """Lightweight view of a running process."""

    pid: int
    name: str
    cpu_percent: float
    memory_percent: float


class SystemSnapshot(TypedDict, total=False):
    """Structured dictionary describing a telemetry sample."""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    net_bytes_sent: int
    net_bytes_recv: int
    uptime_seconds: int
    top_processes: List[ProcessSnapshot]
