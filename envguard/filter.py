"""Filter env vars by pattern, type, or custom predicate."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envguard.schema import EnvSchema, EnvVarType


@dataclass
class FilterResult:
    matched: Dict[str, str]
    excluded: Dict[str, str]
    filter_name: str = "unnamed"

    @property
    def match_count(self) -> int:
        return len(self.matched)

    @property
    def excluded_count(self) -> int:
        return len(self.excluded)

    def __str__(self) -> str:
        lines = [
            f"Filter '{self.filter_name}': {self.match_count} matched, "
            f"{self.excluded_count} excluded",
        ]
        for k, v in self.matched.items():
            lines.append(f"  + {k}={v}")
        return "\n".join(lines)


def filter_env(
    env: Dict[str, str],
    *,
    patterns: Optional[List[str]] = None,
    var_type: Optional[EnvVarType] = None,
    schema: Optional[EnvSchema] = None,
    predicate: Optional[Callable[[str, str], bool]] = None,
    filter_name: str = "unnamed",
) -> FilterResult:
    """Return env vars matching all supplied criteria."""
    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}

    type_keys: Optional[set] = None
    if var_type is not None and schema is not None:
        type_keys = {
            name
            for name, spec in schema.vars.items()
            if spec.type == var_type
        }

    for key, value in env.items():
        if patterns is not None:
            if not any(fnmatch.fnmatch(key, p) for p in patterns):
                excluded[key] = value
                continue

        if type_keys is not None and key not in type_keys:
            excluded[key] = value
            continue

        if predicate is not None and not predicate(key, value):
            excluded[key] = value
            continue

        matched[key] = value

    return FilterResult(matched=matched, excluded=excluded, filter_name=filter_name)
