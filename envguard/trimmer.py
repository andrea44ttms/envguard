"""Trimmer: remove unused or redundant keys from an env dict based on a schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envguard.schema import EnvSchema


@dataclass
class TrimResult:
    """Result of a trim operation."""

    original: Dict[str, str]
    trimmed: Dict[str, str]
    removed_keys: List[str] = field(default_factory=list)

    @property
    def remove_count(self) -> int:
        return len(self.removed_keys)

    def __str__(self) -> str:
        lines = [f"TrimResult: {self.remove_count} key(s) removed"]
        if self.removed_keys:
            for key in sorted(self.removed_keys):
                lines.append(f"  - {key}")
        else:
            lines.append("  (nothing removed)")
        return "\n".join(lines)


def trim_env(
    env: Dict[str, str],
    schema: EnvSchema,
    *,
    remove_undeclared: bool = True,
    remove_empty: bool = False,
) -> TrimResult:
    """Return a new env dict with unwanted keys stripped.

    Args:
        env: The source environment mapping.
        schema: Schema defining declared variables.
        remove_undeclared: When True, keys not present in the schema are removed.
        remove_empty: When True, keys whose value is an empty string are removed.

    Returns:
        A :class:`TrimResult` describing what was kept and what was removed.
    """
    declared_keys = {var.name for var in schema.vars}
    removed: List[str] = []
    trimmed: Dict[str, str] = {}

    for key, value in env.items():
        if remove_undeclared and key not in declared_keys:
            removed.append(key)
            continue
        if remove_empty and value == "":
            removed.append(key)
            continue
        trimmed[key] = value

    return TrimResult(original=dict(env), trimmed=trimmed, removed_keys=removed)
