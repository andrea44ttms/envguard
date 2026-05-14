"""sanitizer.py — Strip, normalize, and clean env values before use."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class SanitizeResult:
    """Result of a sanitization pass over an env dict."""
    original: Dict[str, str]
    sanitized: Dict[str, str]
    changes: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, before, after)

    @property
    def change_count(self) -> int:
        return len(self.changes)

    def __str__(self) -> str:
        if not self.changes:
            return "SanitizeResult: no changes"
        lines = [f"SanitizeResult: {self.change_count} change(s)"]
        for key, before, after in self.changes:
            lines.append(f"  {key}: {before!r} -> {after!r}")
        return "\n".join(lines)


def sanitize_env(
    env: Dict[str, str],
    *,
    strip_whitespace: bool = True,
    remove_null_bytes: bool = True,
    normalize_newlines: bool = True,
    max_value_length: int | None = None,
) -> SanitizeResult:
    """Return a sanitized copy of *env* with a record of every change made.

    Parameters
    ----------
    env:
        Raw environment mapping to sanitize.
    strip_whitespace:
        Strip leading/trailing whitespace from values.
    remove_null_bytes:
        Remove embedded null bytes (``\\x00``) from values.
    normalize_newlines:
        Replace ``\\r\\n`` and bare ``\\r`` with ``\\n``.
    max_value_length:
        Truncate values longer than this limit (``None`` = no limit).
    """
    sanitized: Dict[str, str] = {}
    changes: List[Tuple[str, str, str]] = []

    for key, value in env.items():
        original_value = value
        v = value

        if remove_null_bytes:
            v = v.replace("\x00", "")
        if normalize_newlines:
            v = v.replace("\r\n", "\n").replace("\r", "\n")
        if strip_whitespace:
            v = v.strip()
        if max_value_length is not None and len(v) > max_value_length:
            v = v[:max_value_length]

        sanitized[key] = v
        if v != original_value:
            changes.append((key, original_value, v))

    return SanitizeResult(original=dict(env), sanitized=sanitized, changes=changes)
