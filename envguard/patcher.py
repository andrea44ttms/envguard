"""Patch an existing .env file by applying a dict of updates."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PatchResult:
    """Outcome of a patch operation."""

    updated: Dict[str, str] = field(default_factory=dict)
    added: Dict[str, str] = field(default_factory=dict)
    removed: List[str] = field(default_factory=list)
    original_lines: List[str] = field(default_factory=list, repr=False)
    patched_lines: List[str] = field(default_factory=list, repr=False)

    @property
    def change_count(self) -> int:
        return len(self.updated) + len(self.added) + len(self.removed)

    def __str__(self) -> str:  # pragma: no cover
        parts = []
        if self.updated:
            parts.append(f"Updated ({len(self.updated)}): {', '.join(self.updated)}")
        if self.added:
            parts.append(f"Added ({len(self.added)}): {', '.join(self.added)}")
        if self.removed:
            parts.append(f"Removed ({len(self.removed)}): {', '.join(self.removed)}")
        return "\n".join(parts) if parts else "No changes."


def patch_env(
    source: Dict[str, str],
    updates: Dict[str, str],
    remove_keys: Optional[List[str]] = None,
) -> PatchResult:
    """Apply *updates* and optional *remove_keys* to *source* env dict.

    Returns a :class:`PatchResult` describing what changed together with
    the rendered .env lines so callers can write the result to disk.
    """
    remove_keys = remove_keys or []
    result = PatchResult()

    merged: Dict[str, str] = {}
    for key, value in source.items():
        result.original_lines.append(f"{key}={value}")
        if key in remove_keys:
            result.removed.append(key)
            continue
        if key in updates:
            new_val = updates[key]
            if new_val != value:
                result.updated[key] = new_val
            merged[key] = new_val
        else:
            merged[key] = value

    for key, value in updates.items():
        if key not in source and key not in remove_keys:
            result.added[key] = value
            merged[key] = value

    result.patched_lines = [f"{k}={v}" for k, v in merged.items()]
    return result


def write_patch(path: Path, result: PatchResult) -> None:
    """Write *result.patched_lines* to *path* as a .env file."""
    path.write_text("\n".join(result.patched_lines) + "\n", encoding="utf-8")
