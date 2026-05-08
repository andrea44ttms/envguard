"""Lint .env files for style and best-practice issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envguard.schema import EnvSchema


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str  # "warning" | "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def __str__(self) -> str:
        if not self.issues:
            return "No lint issues found."
        lines = [str(i) for i in self.issues]
        lines.append(f"\n{self.error_count} error(s), {self.warning_count} warning(s).")
        return "\n".join(lines)


def lint_env(env: Dict[str, str], schema: EnvSchema) -> LintResult:
    """Run lint checks on *env* against *schema*."""
    issues: List[LintIssue] = []
    declared_keys = {v.name for v in schema.vars}

    for key, value in env.items():
        # Undeclared keys
        if key not in declared_keys:
            issues.append(LintIssue(key, "Key is not declared in schema.", "warning"))
            continue

        # Whitespace in value
        if value != value.strip():
            issues.append(LintIssue(key, "Value has leading or trailing whitespace.", "warning"))

        # Empty value for declared key
        if value == "":
            issues.append(LintIssue(key, "Value is an empty string.", "warning"))

    for var in schema.vars:
        # Lowercase key names
        if var.name != var.name.upper():
            issues.append(LintIssue(var.name, "Key is not uppercase.", "warning"))

        # Required vars with a default set (contradictory)
        if var.required and var.default is not None:
            issues.append(
                LintIssue(
                    var.name,
                    "Required variable also has a default value — consider making it optional.",
                    "warning",
                )
            )

    return LintResult(issues=issues)
