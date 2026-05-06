"""Diff utility to compare two .env files or env dicts against a schema."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class EnvDiff:
    """Represents the diff between two environment snapshots."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        if self.added:
            lines.append(f"  Added   ({len(self.added)}): {', '.join(self.added.keys())}")
        if self.removed:
            lines.append(f"  Removed ({len(self.removed)}): {', '.join(self.removed.keys())}")
        if self.changed:
            lines.append(f"  Changed ({len(self.changed)}): {', '.join(self.changed.keys())}")
        if not lines:
            return "No differences found."
        return "\n".join(lines)

    def __str__(self) -> str:
        lines = ["EnvDiff:"]
        for key, value in self.added.items():
            lines.append(f"  + {key}={value}")
        for key, value in self.removed.items():
            lines.append(f"  - {key}={value}")
        for key, (old, new) in self.changed.items():
            lines.append(f"  ~ {key}: {old!r} -> {new!r}")
        if not self.has_changes:
            lines.append("  (no changes)")
        return "\n".join(lines)


_SENSITIVE_KEYWORDS = ("secret", "password", "passwd", "token", "key", "api", "auth")


def _redact_if_sensitive(key: str, value: str) -> str:
    lower = key.lower()
    if any(kw in lower for kw in _SENSITIVE_KEYWORDS):
        return "***"
    return value


def diff_envs(
    base: Dict[str, str],
    target: Dict[str, str],
    redact_sensitive: bool = True,
) -> EnvDiff:
    """Compare two env dicts and return an EnvDiff.

    Args:
        base: The original/reference environment mapping.
        target: The new/updated environment mapping.
        redact_sensitive: If True, mask values for sensitive-looking keys.

    Returns:
        An EnvDiff describing the changes from base to target.
    """
    result = EnvDiff()

    all_keys = set(base) | set(target)
    for key in sorted(all_keys):
        in_base = key in base
        in_target = key in target

        if in_target and not in_base:
            val = _redact_if_sensitive(key, target[key]) if redact_sensitive else target[key]
            result.added[key] = val
        elif in_base and not in_target:
            val = _redact_if_sensitive(key, base[key]) if redact_sensitive else base[key]
            result.removed[key] = val
        elif base[key] != target[key]:
            old = _redact_if_sensitive(key, base[key]) if redact_sensitive else base[key]
            new = _redact_if_sensitive(key, target[key]) if redact_sensitive else target[key]
            result.changed[key] = (old, new)
        else:
            result.unchanged.append(key)

    return result
