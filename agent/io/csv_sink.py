"""CSV persistence with local buffering on failure."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

from agent import config
from agent.dto import SystemSnapshot


def _write_csv_rows(csv_path: Path, rows: List[SystemSnapshot]) -> None:
    """Append rows to the CSV, writing the header when needed."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = csv_path.exists()
    with csv_path.open("a", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=config.CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in config.CSV_FIELDS})


def _load_buffer(buffer_path: Path) -> List[SystemSnapshot]:
    if not buffer_path.exists():
        return []
    with buffer_path.open() as buffer_file:
        return [json.loads(line) for line in buffer_file if line.strip()]


def _persist_buffer(buffer_path: Path, rows: List[SystemSnapshot]) -> None:
    buffer_path.parent.mkdir(parents=True, exist_ok=True)
    with buffer_path.open("w") as buffer_file:
        for row in rows:
            buffer_file.write(json.dumps(row) + "\n")


def save_csv(
    stats: SystemSnapshot,
    csv_path: Path | None = None,
    buffer_path: Path | None = None,
) -> bool:
    """Save stats to CSV, buffering locally if the write fails."""
    csv_target = Path(csv_path) if csv_path else config.CSV_PATH
    buffer_target = Path(buffer_path) if buffer_path else config.BUFFER_PATH

    buffered_rows = _load_buffer(buffer_target)
    rows_to_write: List[Dict[str, object]] = buffered_rows + [stats]

    try:
        _write_csv_rows(csv_target, rows_to_write)
        if buffer_target.exists():
            buffer_target.unlink()
        return True
    except OSError:
        _persist_buffer(buffer_target, rows_to_write)
        return False
