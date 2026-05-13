"""Flatten nested prefix-based env vars into a structured dict of dicts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FlattenResult:
    """Result of flattening an env dict by prefix groups."""

    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)
    separator: str = "_"

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    @property
    def total_count(self) -> int:
        total = sum(len(v) for v in self.groups.values())
        return total + len(self.ungrouped)

    def get_group(self, prefix: str) -> Dict[str, str]:
        """Return the sub-dict for a given prefix, or empty dict."""
        return self.groups.get(prefix.upper(), {})

    def __str__(self) -> str:  # pragma: no cover
        lines = []
        for group, members in sorted(self.groups.items()):
            lines.append(f"[{group}]")
            for k, v in sorted(members.items()):
                lines.append(f"  {k} = {v}")
        if self.ungrouped:
            lines.append("[<ungrouped>]")
            for k, v in sorted(self.ungrouped.items()):
                lines.append(f"  {k} = {v}")
        return "\n".join(lines) if lines else "(empty)"


def flatten_env(
    env: Dict[str, str],
    prefixes: Optional[List[str]] = None,
    separator: str = "_",
    strip_prefix: bool = True,
) -> FlattenResult:
    """Group env vars by known prefixes.

    Args:
        env: Raw env dict.
        prefixes: List of prefix strings to group by (case-insensitive).
                  If None, all unique first-segment prefixes are auto-detected.
        separator: Separator between prefix and key name (default ``_``).
        strip_prefix: When True, the stored sub-key omits the prefix portion.

    Returns:
        A :class:`FlattenResult` with grouped and ungrouped vars.
    """
    result = FlattenResult(separator=separator)

    if prefixes is None:
        # Auto-detect: collect all keys that contain the separator
        detected: set[str] = set()
        for key in env:
            upper = key.upper()
            if separator in upper:
                detected.add(upper.split(separator, 1)[0])
        prefixes = list(detected)

    normalised_prefixes = [p.upper() for p in prefixes]

    for key, value in env.items():
        upper_key = key.upper()
        matched = False
        for prefix in normalised_prefixes:
            expected_start = prefix + separator
            if upper_key.startswith(expected_start):
                sub_key = key[len(expected_start):] if strip_prefix else key
                result.groups.setdefault(prefix, {})[sub_key] = value
                matched = True
                break
        if not matched:
            result.ungrouped[key] = value

    return result
