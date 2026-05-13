"""Summarize an environment validation result into a concise, human-readable report."""

from dataclasses import dataclass, field
from typing import List

from envguard.result import ValidationResult
from envguard.schema import EnvSchema, EnvVarType


@dataclass
class EnvSummary:
    total_vars: int
    required_count: int
    optional_count: int
    present_count: int
    missing_required: List[str]
    type_breakdown: dict
    is_valid: bool
    error_messages: List[str] = field(default_factory=list)

    @property
    def missing_required_count(self) -> int:
        return len(self.missing_required)

    @property
    def coverage_pct(self) -> float:
        if self.total_vars == 0:
            return 100.0
        return round((self.present_count / self.total_vars) * 100, 1)

    def __str__(self) -> str:
        lines = [
            "=== Env Summary ===",
            f"  Total declared : {self.total_vars}",
            f"  Required        : {self.required_count}",
            f"  Optional        : {self.optional_count}",
            f"  Present         : {self.present_count}",
            f"  Coverage        : {self.coverage_pct}%",
            f"  Valid           : {'yes' if self.is_valid else 'no'}",
        ]
        if self.missing_required:
            lines.append(f"  Missing required: {', '.join(self.missing_required)}")
        if self.type_breakdown:
            breakdown = ", ".join(f"{k}={v}" for k, v in self.type_breakdown.items())
            lines.append(f"  Types           : {breakdown}")
        if self.error_messages:
            lines.append("  Errors:")
            for msg in self.error_messages:
                lines.append(f"    - {msg}")
        return "\n".join(lines)


def summarize_env(schema: EnvSchema, result: ValidationResult, env: dict) -> EnvSummary:
    """Build an EnvSummary from a schema, validation result, and raw env dict."""
    vars_list = list(schema.vars.values())
    required = [v for v in vars_list if v.required]
    optional = [v for v in vars_list if not v.required]

    present = [name for name in schema.vars if name in env and env[name] != ""]

    missing_required = [
        v.name for v in required if v.name not in env or env[v.name] == ""
    ]

    type_breakdown: dict = {}
    for v in vars_list:
        label = v.var_type.value
        type_breakdown[label] = type_breakdown.get(label, 0) + 1

    error_messages = [str(e) for e in result.errors]

    return EnvSummary(
        total_vars=len(vars_list),
        required_count=len(required),
        optional_count=len(optional),
        present_count=len(present),
        missing_required=missing_required,
        type_breakdown=type_breakdown,
        is_valid=result.is_valid,
        error_messages=error_messages,
    )
