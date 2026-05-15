"""Scope filtering: restrict an env dict to a named deployment scope."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScopeResult:
    """Result of applying a scope filter to an env dict."""

    scope: str
    matched: Dict[str, str] = field(default_factory=dict)
    excluded: List[str] = field(default_factory=list)

    @property
    def match_count(self) -> int:
        return len(self.matched)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded)

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"Scope: {self.scope}",
                 f"  Matched  : {self.match_count}",
                 f"  Excluded : {self.excluded_count}"]
        for k, v in self.matched.items():
            lines.append(f"    {k}={v}")
        return "\n".join(lines)


def scope_env(
    env: Dict[str, str],
    scope: str,
    scope_map: Dict[str, List[str]],
    *,
    include_unscoped: bool = True,
) -> ScopeResult:
    """Return only the env keys that belong to *scope* (or are unscoped).

    Args:
        env: The full environment dictionary.
        scope: The target scope name (e.g. ``"production"``).
        scope_map: Mapping of scope name -> list of key names that belong to it.
            A key listed under *any* scope is considered "scoped".  Keys that
            appear in no scope are treated as unscoped / global.
        include_unscoped: When ``True`` (default) unscoped keys are included in
            the result regardless of the chosen scope.

    Returns:
        :class:`ScopeResult` with the filtered env and excluded key names.
    """
    target_keys: set[str] = set(scope_map.get(scope, []))
    all_scoped: set[str] = {k for keys in scope_map.values() for k in keys}

    matched: Dict[str, str] = {}
    excluded: List[str] = []

    for key, value in env.items():
        is_in_target = key in target_keys
        is_unscoped = key not in all_scoped

        if is_in_target or (include_unscoped and is_unscoped):
            matched[key] = value
        else:
            excluded.append(key)

    return ScopeResult(scope=scope, matched=matched, excluded=sorted(excluded))
