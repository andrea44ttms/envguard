"""Stage-aware env filtering: select variables relevant to a deployment stage."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class StageResult:
    stage: str
    matched: Dict[str, str] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)
    _prefixes: List[str] = field(default_factory=list, repr=False)

    @property
    def match_count(self) -> int:
        return len(self.matched)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded)

    def __str__(self) -> str:  # noqa: D105
        lines = [f"Stage: {self.stage}", f"Matched: {self.match_count}  Excluded: {self.excluded_count}"]
        for k, v in self.matched.items():
            lines.append(f"  {k}={v}")
        return "\n".join(lines)


def stage_env(
    env: Dict[str, str],
    stage: str,
    *,
    stage_prefixes: Optional[Dict[str, List[str]]] = None,
    strip_prefix: bool = True,
) -> StageResult:
    """Return only the env vars that belong to *stage*.

    A variable belongs to a stage when its key starts with one of the
    prefixes registered for that stage (case-insensitive).  If no
    ``stage_prefixes`` mapping is supplied a sensible default is used.
    """
    defaults: Dict[str, List[str]] = {
        "production": ["PROD_", "PRODUCTION_"],
        "staging": ["STAGING_", "STG_"],
        "development": ["DEV_", "DEVELOPMENT_", "LOCAL_"],
        "test": ["TEST_", "TESTING_"],
    }
    mapping = stage_prefixes if stage_prefixes is not None else defaults
    prefixes: List[str] = [p.upper() for p in mapping.get(stage.lower(), [])]

    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}

    for key, value in env.items():
        upper_key = key.upper()
        hit_prefix: Optional[str] = None
        for prefix in prefixes:
            if upper_key.startswith(prefix):
                hit_prefix = prefix
                break
        if hit_prefix is not None:
            new_key = key[len(hit_prefix):] if strip_prefix else key
            matched[new_key] = value
        else:
            excluded[key] = value

    result = StageResult(stage=stage, matched=matched, excluded=excluded)
    result._prefixes = prefixes
    return result
