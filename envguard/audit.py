"""Audit helpers — detect undeclared variables and redact sensitive values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from envguard.schema import EnvSchema

_SENSITIVE_KEYWORDS = {"password", "secret", "token", "key", "auth", "credential"}


@dataclass
class AuditReport:
    undeclared: List[str] = field(default_factory=list)
    redacted_snapshot: Dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = ["=== envguard Audit Report ==="]
        if self.undeclared:
            lines.append(f"Undeclared variables ({len(self.undeclared)}):")
            for var in sorted(self.undeclared):
                lines.append(f"  - {var}")
        else:
            lines.append("No undeclared variables found.")
        lines.append("Snapshot (sensitive values redacted):")
        for k, v in sorted(self.redacted_snapshot.items()):
            lines.append(f"  {k}={v}")
        return "\n".join(lines)


def _is_sensitive(name: str) -> bool:
    lower = name.lower()
    return any(kw in lower for kw in _SENSITIVE_KEYWORDS)


def audit_env(schema: EnvSchema, env: Dict[str, str]) -> AuditReport:
    """Compare env against schema; flag undeclared vars and build a redacted snapshot."""
    declared: Set[str] = set(schema.vars.keys())
    present: Set[str] = set(env.keys())

    undeclared = sorted(present - declared)

    redacted: Dict[str, str] = {}
    for key, value in env.items():
        if key not in declared:
            continue
        redacted[key] = "***REDACTED***" if _is_sensitive(key) else value

    return AuditReport(undeclared=undeclared, redacted_snapshot=redacted)
