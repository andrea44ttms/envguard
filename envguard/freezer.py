"""Freeze a validated env snapshot to a file and restore/compare it later."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from envguard.redactor import is_sensitive, redact_value


@dataclass
class FrozenEnv:
    """A point-in-time frozen copy of an env mapping."""

    captured_at: str
    values: Dict[str, str]
    redacted_keys: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "captured_at": self.captured_at,
            "values": self.values,
            "redacted_keys": self.redacted_keys,
        }

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"Frozen at: {self.captured_at}"]
        for k, v in self.values.items():
            lines.append(f"  {k}={v}")
        return "\n".join(lines)


def freeze_env(
    env: Dict[str, str],
    redact: bool = True,
) -> FrozenEnv:
    """Create a FrozenEnv from *env*, optionally redacting sensitive values."""
    captured_at = datetime.now(timezone.utc).isoformat()
    values: Dict[str, str] = {}
    redacted_keys: list = []

    for k, v in env.items():
        if redact and is_sensitive(k):
            values[k] = redact_value(v)
            redacted_keys.append(k)
        else:
            values[k] = v

    return FrozenEnv(captured_at=captured_at, values=values, redacted_keys=redacted_keys)


def save_freeze(frozen: FrozenEnv, path: str | Path) -> None:
    """Persist *frozen* as JSON to *path*."""
    Path(path).write_text(json.dumps(frozen.to_dict(), indent=2), encoding="utf-8")


def load_freeze(path: str | Path) -> FrozenEnv:
    """Load a previously saved FrozenEnv from *path*."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return FrozenEnv(
        captured_at=raw["captured_at"],
        values=raw["values"],
        redacted_keys=raw.get("redacted_keys", []),
    )


def diff_frozen(
    frozen: FrozenEnv,
    current: Dict[str, str],
    redact: bool = True,
) -> Dict[str, dict]:
    """Return a dict of keys that changed between *frozen* and *current*."""
    changes: Dict[str, dict] = {}
    all_keys = set(frozen.values) | set(current)

    for key in all_keys:
        old = frozen.values.get(key)
        new = current.get(key)
        if old != new:
            display_new = redact_value(new) if (redact and new and is_sensitive(key)) else new
            changes[key] = {"before": old, "after": display_new}

    return changes
