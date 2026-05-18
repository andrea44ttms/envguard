"""Archive env snapshots to timestamped files for historical tracking."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envguard.redactor import redact_env


@dataclass
class ArchiveEntry:
    timestamp: str
    path: str
    key_count: int
    redacted: bool

    def __str__(self) -> str:
        tag = " [redacted]" if self.redacted else ""
        return f"{self.timestamp}  {self.path}  ({self.key_count} keys){tag}"


@dataclass
class ArchiveResult:
    entry: ArchiveEntry
    env: Dict[str, str]

    @property
    def ok(self) -> bool:
        return self.entry.key_count >= 0

    def __str__(self) -> str:
        return str(self.entry)


@dataclass
class ArchiveIndex:
    directory: str
    entries: List[ArchiveEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)

    def latest(self) -> Optional[ArchiveEntry]:
        return self.entries[-1] if self.entries else None

    def __str__(self) -> str:
        if not self.entries:
            return f"Archive: {self.directory} (empty)"
        lines = [f"Archive: {self.directory} ({self.count} entries)"]
        for e in self.entries:
            lines.append(f"  {e}")
        return "\n".join(lines)


def archive_env(
    env: Dict[str, str],
    directory: str,
    redact: bool = True,
    prefix: str = "envguard",
) -> ArchiveResult:
    """Save a timestamped archive of the env dict to *directory*."""
    Path(directory).mkdir(parents=True, exist_ok=True)
    stored = redact_env(env) if redact else dict(env)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{prefix}_{ts}.json"
    filepath = os.path.join(directory, filename)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump({"timestamp": ts, "env": stored}, fh, indent=2)
    entry = ArchiveEntry(timestamp=ts, path=filepath, key_count=len(stored), redacted=redact)
    return ArchiveResult(entry=entry, env=stored)


def load_archive_index(directory: str) -> ArchiveIndex:
    """Scan *directory* and return an index of all archived env files."""
    entries: List[ArchiveEntry] = []
    base = Path(directory)
    if base.is_dir():
        for fp in sorted(base.glob("*.json")):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                ts = data.get("timestamp", "unknown")
                kc = len(data.get("env", {}))
                entries.append(ArchiveEntry(timestamp=ts, path=str(fp), key_count=kc, redacted=False))
            except (json.JSONDecodeError, OSError):
                continue
    return ArchiveIndex(directory=directory, entries=entries)
