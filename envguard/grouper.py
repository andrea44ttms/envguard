"""Group env variables by prefix or custom category for organized reporting."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envguard.schema import EnvSchema


@dataclass
class EnvGroup:
    name: str
    keys: List[str] = field(default_factory=list)
    values: Dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.keys)

    def __str__(self) -> str:
        lines = [f"[{self.name}] ({len(self.keys)} vars)"]
        for k in sorted(self.keys):
            lines.append(f"  {k}={self.values.get(k, '')}")
        return "\n".join(lines)


@dataclass
class GroupResult:
    groups: Dict[str, EnvGroup] = field(default_factory=dict)
    ungrouped: EnvGroup = field(default_factory=lambda: EnvGroup(name="ungrouped"))

    @property
    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    @property
    def total_grouped(self) -> int:
        return sum(len(g) for g in self.groups.values())

    def __str__(self) -> str:
        parts = [str(g) for g in self.groups.values()]
        if self.ungrouped.keys:
            parts.append(str(self.ungrouped))
        return "\n".join(parts)


def group_by_prefix(
    env: Dict[str, str],
    schema: Optional[EnvSchema] = None,
    separator: str = "_",
    min_prefix_length: int = 2,
) -> GroupResult:
    """Group env vars by their common prefix (e.g. DB_, AWS_, APP_)."""
    result = GroupResult()
    declared_keys = set(schema.vars.keys()) if schema else set(env.keys())

    for key, value in env.items():
        if key not in declared_keys and schema is not None:
            continue
        parts = key.split(separator, 1)
        prefix = parts[0] if len(parts) > 1 and len(parts[0]) >= min_prefix_length else None
        if prefix:
            if prefix not in result.groups:
                result.groups[prefix] = EnvGroup(name=prefix)
            result.groups[prefix].keys.append(key)
            result.groups[prefix].values[key] = value
        else:
            result.ungrouped.keys.append(key)
            result.ungrouped.values[key] = value

    return result


def group_by_categories(
    env: Dict[str, str],
    categories: Dict[str, List[str]],
) -> GroupResult:
    """Group env vars by explicitly defined category -> key mappings."""
    result = GroupResult()
    categorised: set = set()

    for category, keys in categories.items():
        grp = EnvGroup(name=category)
        for key in keys:
            if key in env:
                grp.keys.append(key)
                grp.values[key] = env[key]
                categorised.add(key)
        if grp.keys:
            result.groups[category] = grp

    for key, value in env.items():
        if key not in categorised:
            result.ungrouped.keys.append(key)
            result.ungrouped.values[key] = value

    return result
