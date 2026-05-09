"""envguard.scorer — Score an environment's completeness and quality against a schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envguard.schema import EnvSchema, EnvVarType
from envguard.result import ValidationResult


@dataclass
class EnvScore:
    """Numeric quality score for a validated environment."""

    total: int
    present: int
    required_present: int
    required_total: int
    optional_present: int
    optional_total: int
    type_errors: int
    constraint_errors: int
    breakdown: Dict[str, float] = field(default_factory=dict)

    @property
    def completeness(self) -> float:
        """Fraction of all declared vars that are present (0.0–1.0)."""
        return self.present / self.total if self.total else 1.0

    @property
    def required_coverage(self) -> float:
        """Fraction of required vars that are present (0.0–1.0)."""
        return self.required_present / self.required_total if self.required_total else 1.0

    @property
    def score(self) -> float:
        """Weighted quality score in the range 0–100."""
        penalty = (self.type_errors + self.constraint_errors) * 5
        raw = (
            self.required_coverage * 60
            + self.completeness * 30
            + max(0, 10 - penalty)
        )
        return round(min(max(raw, 0.0), 100.0), 2)

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            f"EnvScore: {self.score}/100",
            f"  Completeness      : {self.completeness:.0%} ({self.present}/{self.total})",
            f"  Required coverage : {self.required_coverage:.0%} ({self.required_present}/{self.required_total})",
            f"  Type errors       : {self.type_errors}",
            f"  Constraint errors : {self.constraint_errors}",
        ]
        return "\n".join(lines)


def score_env(env: Dict[str, str], schema: EnvSchema, result: ValidationResult) -> EnvScore:
    """Compute an :class:`EnvScore` from a raw env dict and its validation result."""
    total = len(schema.vars)
    required_vars = [v for v in schema.vars.values() if v.required]
    optional_vars = [v for v in schema.vars.values() if not v.required]

    present = sum(1 for k in schema.vars if k in env and env[k] != "")
    required_present = sum(1 for v in required_vars if v.name in env and env[v.name] != "")
    optional_present = sum(1 for v in optional_vars if v.name in env and env[v.name] != "")

    type_errors = sum(
        1 for e in result.errors if "invalid" in e.message.lower() or "cannot" in e.message.lower()
    )
    constraint_errors = sum(
        1 for e in result.errors
        if any(kw in e.message.lower() for kw in ("min", "max", "pattern", "allowed"))
    )

    breakdown = {
        "completeness": round(present / total if total else 1.0, 4),
        "required_coverage": round(required_present / len(required_vars) if required_vars else 1.0, 4),
    }

    return EnvScore(
        total=total,
        present=present,
        required_present=required_present,
        required_total=len(required_vars),
        optional_present=optional_present,
        optional_total=len(optional_vars),
        type_errors=type_errors,
        constraint_errors=constraint_errors,
        breakdown=breakdown,
    )
