"""Deprecation tracker for .env variables.

Flags variables that are declared as deprecated in the schema,
allowing teams to audit and phase out legacy configuration keys.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envguard.schema import EnvSchema
from envguard.redactor import is_sensitive


@dataclass
class DeprecationWarning_:  # noqa: N801  (avoid shadowing built-in)
    key: str
    value: Optional[str]
    message: str
    redacted: bool = False

    def __str__(self) -> str:
        display = "[REDACTED]" if self.redacted else repr(self.value)
        return f"DEPRECATED  {self.key}={display}  — {self.message}"


@dataclass
class DeprecationReport:
    warnings: List[DeprecationWarning_] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.warnings)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    def keys(self) -> List[str]:
        return [w.key for w in self.warnings]

    def __str__(self) -> str:
        if not self.has_warnings:
            return "No deprecated variables found."
        lines = [f"Deprecated variables ({self.count}):"] + [
            f"  {w}" for w in self.warnings
        ]
        return "\n".join(lines)


def check_deprecations(
    env: Dict[str, str],
    schema: EnvSchema,
    *,
    redact: bool = True,
) -> DeprecationReport:
    """Return a DeprecationReport for any deprecated keys present in *env*.

    Args:
        env: Mapping of variable names to raw string values.
        schema: The EnvSchema that may carry ``deprecated`` metadata on vars.
        redact: When *True* (default) sensitive values are hidden.
    """
    warnings: List[DeprecationWarning_] = []

    for var in schema.vars:
        meta: dict = var.metadata or {}
        deprecated_msg: Optional[str] = meta.get("deprecated")
        if deprecated_msg and var.name in env:
            sensitive = redact and is_sensitive(var.name)
            warnings.append(
                DeprecationWarning_(
                    key=var.name,
                    value=None if sensitive else env[var.name],
                    message=deprecated_msg,
                    redacted=sensitive,
                )
            )

    return DeprecationReport(warnings=warnings)
