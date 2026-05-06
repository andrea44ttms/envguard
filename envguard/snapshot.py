"""Snapshot module: capture and compare env validation states over time."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class EnvSnapshot:
    """A point-in-time capture of validated environment variable values."""

    timestamp: str
    values: Dict[str, str]
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "is_valid": self.is_valid,
            "values": self.values,
            "errors": self.errors,
        }

    def __str__(self) -> str:
        status = "VALID" if self.is_valid else f"INVALID ({len(self.errors)} errors)"
        return f"EnvSnapshot [{self.timestamp}] — {status}, {len(self.values)} vars"


def take_snapshot(
    env: Dict[str, str],
    errors: Optional[List[str]] = None,
    redact_keys: Optional[List[str]] = None,
) -> EnvSnapshot:
    """Capture a snapshot of env values, optionally redacting sensitive keys."""
    redact_keys = [k.upper() for k in (redact_keys or [])]
    safe_values = {
        k: ("***" if k.upper() in redact_keys else v)
        for k, v in env.items()
    }
    return EnvSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(),
        values=safe_values,
        errors=list(errors or []),
    )


def save_snapshot(snapshot: EnvSnapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(path: str) -> EnvSnapshot:
    """Load a previously saved snapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return EnvSnapshot(
        timestamp=data["timestamp"],
        values=data["values"],
        errors=data.get("errors", []),
    )


def diff_snapshots(old: EnvSnapshot, new: EnvSnapshot) -> Dict[str, dict]:
    """Return a mapping of keys that changed between two snapshots."""
    all_keys = set(old.values) | set(new.values)
    changes: Dict[str, dict] = {}
    for key in sorted(all_keys):
        old_val = old.values.get(key)
        new_val = new.values.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}
    return changes
