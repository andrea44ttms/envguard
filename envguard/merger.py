"""Merge multiple .env sources with priority-based override support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class MergeSource:
    """Represents a single .env source with a given priority (higher wins)."""

    name: str
    env: Dict[str, str]
    priority: int = 0


@dataclass
class MergeResult:
    """Result of merging multiple env sources."""

    merged: Dict[str, str] = field(default_factory=dict)
    origins: Dict[str, str] = field(default_factory=dict)  # key -> source name
    conflicts: List[Tuple[str, List[str]]] = field(default_factory=list)  # key -> [source names]

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)

    def origin_of(self, key: str) -> Optional[str]:
        """Return the source name that won for a given key."""
        return self.origins.get(key)

    def __str__(self) -> str:
        lines = [f"Merged {len(self.merged)} keys from multiple sources."]
        if self.conflicts:
            lines.append(f"Conflicts resolved ({len(self.conflicts)}):")
            for key, sources in self.conflicts:
                winner = self.origins.get(key, "unknown")
                lines.append(f"  {key}: contested by {sources}, won by '{winner}'")
        return "\n".join(lines)


def merge_envs(*sources: MergeSource) -> MergeResult:
    """Merge env dicts from multiple sources; higher priority wins on conflict."""
    sorted_sources = sorted(sources, key=lambda s: s.priority)

    merged: Dict[str, str] = {}
    origins: Dict[str, str] = {}
    seen: Dict[str, List[str]] = {}

    for source in sorted_sources:
        for key, value in source.env.items():
            if key in seen:
                seen[key].append(source.name)
            else:
                seen[key] = [source.name]
            # Higher priority always overwrites
            merged[key] = value
            origins[key] = source.name

    conflicts = [
        (key, names)
        for key, names in seen.items()
        if len(names) > 1
    ]

    return MergeResult(merged=merged, origins=origins, conflicts=conflicts)
