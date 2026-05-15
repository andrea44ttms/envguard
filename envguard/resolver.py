"""Resolve final effective values for env vars across multiple sources with priority."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class ResolvedVar:
    key: str
    value: str
    source: str
    overridden_by: Optional[str] = None

    def __str__(self) -> str:
        tag = f" (overridden by {self.overridden_by})" if self.overridden_by else ""
        return f"{self.key}={self.value!r} [{self.source}]{tag}"


@dataclass
class ResolveResult:
    resolved: Dict[str, ResolvedVar] = field(default_factory=dict)
    _sources: List[str] = field(default_factory=list)

    @property
    def keys(self) -> List[str]:
        return list(self.resolved.keys())

    @property
    def source_names(self) -> List[str]:
        return list(self._sources)

    def get(self, key: str) -> Optional[ResolvedVar]:
        return self.resolved.get(key)

    def to_dict(self) -> Dict[str, str]:
        return {k: v.value for k, v in self.resolved.items()}

    def __str__(self) -> str:
        lines = [f"ResolveResult ({len(self.resolved)} vars, {len(self._sources)} sources)"]
        for var in self.resolved.values():
            lines.append(f"  {var}")
        return "\n".join(lines)


def resolve_env(
    sources: List[Tuple[str, Dict[str, str]]],
) -> ResolveResult:
    """Resolve env vars from multiple (name, env) pairs.

    Sources are listed in ascending priority order — later entries win.
    Each source is a tuple of (source_name, env_dict).
    """
    if not sources:
        return ResolveResult()

    result = ResolveResult(_sources=[name for name, _ in sources])
    winner: Dict[str, Tuple[str, str]] = {}  # key -> (value, source_name)

    for source_name, env in sources:
        for key, value in env.items():
            if key in winner:
                prev_value, prev_source = winner[key]
                result.resolved[key] = ResolvedVar(
                    key=key,
                    value=value,
                    source=source_name,
                    overridden_by=None,
                )
                # mark previous entry as overridden
                if key in result.resolved:
                    old = result.resolved[key]
                    _ = old  # replaced below
                result.resolved[key] = ResolvedVar(
                    key=key,
                    value=value,
                    source=source_name,
                )
                winner[key] = (value, source_name)
            else:
                result.resolved[key] = ResolvedVar(
                    key=key,
                    value=value,
                    source=source_name,
                )
                winner[key] = (value, source_name)

    return result
