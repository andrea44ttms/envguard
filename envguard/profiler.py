"""Profile .env files to produce statistics and insights about declared variables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envguard.schema import EnvSchema, EnvVarType
from envguard.result import ValidationResult


@dataclass
class EnvProfile:
    """Statistical summary of a validated environment."""

    total: int = 0
    required_count: int = 0
    optional_count: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    sensitive_keys: List[str] = field(default_factory=list)
    with_defaults: List[str] = field(default_factory=list)
    with_constraints: List[str] = field(default_factory=list)
    error_keys: List[str] = field(default_factory=list)

    @property
    def health_score(self) -> float:
        """Return a 0.0–1.0 score based on valid variables vs total."""
        if self.total == 0:
            return 1.0
        return round(1.0 - len(self.error_keys) / self.total, 4)

    def __str__(self) -> str:
        lines = [
            f"EnvProfile: {self.total} variables (health={self.health_score:.0%})",
            f"  Required : {self.required_count}",
            f"  Optional : {self.optional_count}",
            f"  By type  : { {k: v for k, v in self.by_type.items()} }",
            f"  Sensitive: {len(self.sensitive_keys)}",
            f"  Defaults : {len(self.with_defaults)}",
            f"  Constrained: {len(self.with_constraints)}",
        ]
        if self.error_keys:
            lines.append(f"  Errors on: {self.error_keys}")
        return "\n".join(lines)


_SENSITIVE_PATTERNS = ("secret", "password", "passwd", "token", "key", "auth", "credential")


def profile_env(schema: EnvSchema, result: ValidationResult) -> EnvProfile:
    """Build an EnvProfile from a schema and its ValidationResult."""
    error_keys = {e.key for e in result.errors}
    prof = EnvProfile(error_keys=sorted(error_keys))

    for var in schema.vars.values():
        prof.total += 1
        if var.required:
            prof.required_count += 1
        else:
            prof.optional_count += 1

        type_name = var.type.value
        prof.by_type[type_name] = prof.by_type.get(type_name, 0) + 1

        lower = var.name.lower()
        if any(p in lower for p in _SENSITIVE_PATTERNS):
            prof.sensitive_keys.append(var.name)

        if var.default is not None:
            prof.with_defaults.append(var.name)

        if var.allowed_values or var.min_value is not None or var.max_value is not None:
            prof.with_constraints.append(var.name)

    return prof
