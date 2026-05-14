"""envguard.pinner — Pin current env values to a lockfile for drift detection."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envguard.redactor import is_sensitive, redact_value


@dataclass
class PinEntry:
    key: str
    value: str
    redacted: bool = False

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "redacted": self.redacted}


@dataclass
class PinResult:
    entries: List[PinEntry] = field(default_factory=list)
    pinned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = ""

    @property
    def count(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict:
        return {
            "pinned_at": self.pinned_at,
            "source": self.source,
            "entries": [e.to_dict() for e in self.entries],
        }

    def __str__(self) -> str:
        lines = [f"# Pinned {self.count} variable(s) at {self.pinned_at}"]
        for e in self.entries:
            lines.append(f"{e.key}={e.value}")
        return "\n".join(lines)


def pin_env(
    env: Dict[str, str],
    redact: bool = True,
    source: str = "",
) -> PinResult:
    """Create a PinResult capturing the current state of *env*."""
    entries: List[PinEntry] = []
    for key, raw_value in sorted(env.items()):
        sensitive = is_sensitive(key)
        value = redact_value(raw_value) if (redact and sensitive) else raw_value
        entries.append(PinEntry(key=key, value=value, redacted=redact and sensitive))
    return PinResult(entries=entries, source=source)


def save_pin(result: PinResult, path: str) -> None:
    """Persist *result* as a JSON lockfile at *path*."""
    Path(path).write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")


def load_pin(path: str) -> Optional[PinResult]:
    """Load a previously saved PinResult from *path*. Returns None if file absent."""
    p = Path(path)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    entries = [PinEntry(**e) for e in data.get("entries", [])]
    return PinResult(
        entries=entries,
        pinned_at=data.get("pinned_at", ""),
        source=data.get("source", ""),
    )


def diff_pin(current: PinResult, previous: PinResult) -> Dict[str, dict]:
    """Return a mapping of keys that changed between two PinResults."""
    prev_map = {e.key: e.value for e in previous.entries}
    curr_map = {e.key: e.value for e in current.entries}
    all_keys = set(prev_map) | set(curr_map)
    changes: Dict[str, dict] = {}
    for key in sorted(all_keys):
        old = prev_map.get(key)
        new = curr_map.get(key)
        if old != new:
            changes[key] = {"old": old, "new": new}
    return changes
