"""Sort and order environment variables by various criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from envguard.schema import EnvSchema


class SortOrder(str, Enum):
    ALPHA = "alpha"          # alphabetical by key
    TYPE = "type"            # grouped by EnvVarType
    REQUIRED_FIRST = "required"  # required vars before optional
    DECLARATION = "declaration"  # original schema declaration order


@dataclass
class SortResult:
    order: SortOrder
    sorted_env: Dict[str, str]
    original_env: Dict[str, str]
    sections: Dict[str, List[str]] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover
        lines = [f"Sort order : {self.order.value}",
                 f"Variables  : {len(self.sorted_env)}"]
        if self.sections:
            for section, keys in self.sections.items():
                lines.append(f"  [{section}] {', '.join(keys)}")
        return "\n".join(lines)


def _alpha_sort(env: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    sorted_keys = sorted(env.keys())
    return {k: env[k] for k in sorted_keys}, {}


def _type_sort(
    env: Dict[str, str], schema: EnvSchema
) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    buckets: Dict[str, List[str]] = {}
    schema_map = {v.name: v for v in schema.vars}
    for key in env:
        var = schema_map.get(key)
        bucket = var.type.value if var else "unknown"
        buckets.setdefault(bucket, []).append(key)
    sorted_env: Dict[str, str] = {}
    for bucket in sorted(buckets):
        for k in sorted(buckets[bucket]):
            sorted_env[k] = env[k]
    return sorted_env, buckets


def _required_first_sort(
    env: Dict[str, str], schema: EnvSchema
) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    schema_map = {v.name: v for v in schema.vars}
    required, optional, unknown = [], [], []
    for key in sorted(env.keys()):
        var = schema_map.get(key)
        if var is None:
            unknown.append(key)
        elif var.required:
            required.append(key)
        else:
            optional.append(key)
    sections = {"required": required, "optional": optional, "unknown": unknown}
    sorted_env = {k: env[k] for group in (required, optional, unknown) for k in group}
    return sorted_env, {k: v for k, v in sections.items() if v}


def _declaration_sort(
    env: Dict[str, str], schema: EnvSchema
) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
    declared_order = [v.name for v in schema.vars if v.name in env]
    undeclared = [k for k in env if k not in {v.name for v in schema.vars}]
    all_keys = declared_order + sorted(undeclared)
    return {k: env[k] for k in all_keys}, {}


def sort_env(
    env: Dict[str, str],
    schema: EnvSchema,
    order: SortOrder = SortOrder.ALPHA,
) -> SortResult:
    """Return a SortResult with variables ordered by *order*."""
    if order == SortOrder.ALPHA:
        sorted_env, sections = _alpha_sort(env)
    elif order == SortOrder.TYPE:
        sorted_env, sections = _type_sort(env, schema)
    elif order == SortOrder.REQUIRED_FIRST:
        sorted_env, sections = _required_first_sort(env, schema)
    else:
        sorted_env, sections = _declaration_sort(env, schema)
    return SortResult(order=order, sorted_env=sorted_env, original_env=env, sections=sections)
