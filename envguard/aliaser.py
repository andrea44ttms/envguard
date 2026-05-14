"""aliaser.py — Map environment variable aliases to canonical names."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AliasMapping:
    """A single alias → canonical name mapping."""

    alias: str
    canonical: str
    description: Optional[str] = None

    def __str__(self) -> str:
        desc = f" ({self.description})" if self.description else ""
        return f"{self.alias} -> {self.canonical}{desc}"


@dataclass
class AliasResult:
    """Result of resolving aliases in an env dict."""

    resolved: Dict[str, str]
    applied: List[AliasMapping] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def apply_count(self) -> int:
        return len(self.applied)

    def __str__(self) -> str:
        lines = [f"AliasResult: {self.apply_count} applied, {len(self.skipped)} skipped"]
        for mapping in self.applied:
            lines.append(f"  applied : {mapping}")
        for alias in self.skipped:
            lines.append(f"  skipped : {alias} (canonical already present)")
        return "\n".join(lines)


def resolve_aliases(
    env: Dict[str, str],
    mappings: List[AliasMapping],
    *,
    overwrite: bool = False,
) -> AliasResult:
    """Resolve alias keys in *env* to their canonical names.

    For each mapping, if the alias key exists in *env* and the canonical key
    does not (or *overwrite* is True), the alias value is copied to the
    canonical key and the alias key is removed.

    Args:
        env: Source environment dictionary (not mutated).
        mappings: Ordered list of :class:`AliasMapping` objects.
        overwrite: When True, canonical key is overwritten even if already set.

    Returns:
        :class:`AliasResult` with the resolved env and audit information.
    """
    resolved = dict(env)
    applied: List[AliasMapping] = []
    skipped: List[str] = []

    for mapping in mappings:
        alias = mapping.alias
        canonical = mapping.canonical

        if alias not in resolved:
            continue

        if canonical in resolved and not overwrite:
            skipped.append(alias)
            continue

        resolved[canonical] = resolved.pop(alias)
        applied.append(mapping)

    return AliasResult(resolved=resolved, applied=applied, skipped=skipped)
