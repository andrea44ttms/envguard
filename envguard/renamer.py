"""Rename environment variable keys according to a mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RenameResult:
    """Result of a rename operation."""
    original: Dict[str, str]
    renamed: Dict[str, str]
    applied: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: Dict[str, str] = field(default_factory=dict)   # old_key -> reason

    @property
    def rename_count(self) -> int:
        return len(self.applied)

    def __str__(self) -> str:
        lines = [f"RenameResult: {self.rename_count} rename(s) applied, {len(self.skipped)} skipped"]
        for old, new in self.applied.items():
            lines.append(f"  {old} -> {new}")
        for key, reason in self.skipped.items():
            lines.append(f"  SKIPPED {key}: {reason}")
        return "\n".join(lines)


def rename_env(
    env: Dict[str, str],
    mapping: Dict[str, str],
    overwrite: bool = False,
) -> RenameResult:
    """Rename keys in *env* according to *mapping* (old_key -> new_key).

    Args:
        env: Source environment dictionary.
        mapping: Dict mapping old key names to new key names.
        overwrite: If True, allow renaming even when the new key already exists
                   (the existing value will be replaced). Defaults to False.

    Returns:
        A :class:`RenameResult` describing what was changed.
    """
    result: Dict[str, str] = dict(env)
    applied: Dict[str, str] = {}
    skipped: Dict[str, str] = {}

    for old_key, new_key in mapping.items():
        if old_key not in result:
            skipped[old_key] = "key not present in env"
            continue
        if new_key in result and not overwrite:
            skipped[old_key] = f"target key '{new_key}' already exists"
            continue
        value = result.pop(old_key)
        result[new_key] = value
        applied[old_key] = new_key

    return RenameResult(
        original=dict(env),
        renamed=result,
        applied=applied,
        skipped=skipped,
    )
