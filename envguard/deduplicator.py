"""Detect and remove duplicate values across env variables."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class DuplicateGroup:
    """A set of keys that share the same value."""

    value: str
    keys: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        keys_str = ", ".join(self.keys)
        return f"[{keys_str}] => {self.value!r}"


@dataclass
class DeduplicationResult:
    """Result of a deduplication scan."""

    env: Dict[str, str]
    duplicate_groups: List[DuplicateGroup] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)

    @property
    def duplicate_count(self) -> int:
        """Total number of keys involved in duplicates."""
        return sum(len(g.keys) for g in self.duplicate_groups)

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicate_groups) > 0

    def __str__(self) -> str:
        if not self.has_duplicates:
            return "No duplicate values found."
        lines = [f"Duplicate groups ({len(self.duplicate_groups)}):"]
        for group in self.duplicate_groups:
            lines.append(f"  {group}")
        if self.removed_keys:
            lines.append(f"Removed keys: {', '.join(self.removed_keys)}")
        return "\n".join(lines)


def deduplicate_env(
    env: Dict[str, str],
    keep: str = "first",
    ignore_keys: Set[str] | None = None,
) -> DeduplicationResult:
    """Scan *env* for keys sharing identical values.

    Args:
        env: The environment mapping to inspect.
        keep: Which key to retain when deduplicating — ``"first"`` keeps the
            key that appears first in iteration order; ``"none"`` removes all
            duplicates from the returned env.
        ignore_keys: Keys to exclude from duplicate detection.

    Returns:
        A :class:`DeduplicationResult` with the cleaned env and metadata.
    """
    ignore_keys = ignore_keys or set()

    # Build value -> keys index
    value_index: Dict[str, List[str]] = {}
    for key, val in env.items():
        if key in ignore_keys:
            continue
        value_index.setdefault(val, []).append(key)

    duplicate_groups = [
        DuplicateGroup(value=val, keys=keys)
        for val, keys in value_index.items()
        if len(keys) > 1
    ]

    removed_keys: List[str] = []
    cleaned: Dict[str, str] = dict(env)

    for group in duplicate_groups:
        if keep == "first":
            # Remove all but the first occurrence
            for key in group.keys[1:]:
                cleaned.pop(key, None)
                removed_keys.append(key)
        elif keep == "none":
            for key in group.keys:
                cleaned.pop(key, None)
                removed_keys.append(key)

    return DeduplicationResult(
        env=cleaned,
        duplicate_groups=duplicate_groups,
        removed_keys=removed_keys,
    )
