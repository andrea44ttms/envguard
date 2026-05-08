"""Compare two sets of env vars against a schema and report structural differences."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envguard.schema import EnvSchema
from envguard.redactor import is_sensitive, redact_value


@dataclass
class EnvComparison:
    """Result of comparing two env mappings against a shared schema."""

    only_in_left: Dict[str, str] = field(default_factory=dict)
    only_in_right: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (left_val, right_val)
    common: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_left or self.only_in_right or self.changed)

    def summary(self) -> str:
        lines = []
        lines.append(f"Only in left  : {len(self.only_in_left)}")
        lines.append(f"Only in right : {len(self.only_in_right)}")
        lines.append(f"Changed       : {len(self.changed)}")
        lines.append(f"Common        : {len(self.common)}")
        return "\n".join(lines)

    def __str__(self) -> str:
        parts = [self.summary()]
        if self.only_in_left:
            parts.append("\n[Only in left]")
            for k, v in self.only_in_left.items():
                parts.append(f"  {k}={v}")
        if self.only_in_right:
            parts.append("\n[Only in right]")
            for k, v in self.only_in_right.items():
                parts.append(f"  {k}={v}")
        if self.changed:
            parts.append("\n[Changed]")
            for k, (lv, rv) in self.changed.items():
                parts.append(f"  {k}: {lv!r} -> {rv!r}")
        return "\n".join(parts)


def compare_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    schema: Optional[EnvSchema] = None,
) -> EnvComparison:
    """Compare two env dicts, redacting sensitive values when a schema is provided."""

    def _maybe_redact(key: str, value: str) -> str:
        if schema is not None and is_sensitive(key):
            return redact_value(value)
        return value

    all_keys = set(left) | set(right)
    only_in_left: Dict[str, str] = {}
    only_in_right: Dict[str, str] = {}
    changed: Dict[str, tuple] = {}
    common: List[str] = []

    for key in sorted(all_keys):
        in_left = key in left
        in_right = key in right
        if in_left and not in_right:
            only_in_left[key] = _maybe_redact(key, left[key])
        elif in_right and not in_left:
            only_in_right[key] = _maybe_redact(key, right[key])
        else:
            lv, rv = left[key], right[key]
            if lv != rv:
                changed[key] = (_maybe_redact(key, lv), _maybe_redact(key, rv))
            else:
                common.append(key)

    return EnvComparison(
        only_in_left=only_in_left,
        only_in_right=only_in_right,
        changed=changed,
        common=common,
    )
