"""Chain multiple validation passes and collect aggregated results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envguard.schema import EnvSchema
from envguard.validator import EnvValidator
from envguard.result import ValidationResult, ValidationError


@dataclass
class ChainStep:
    name: str
    schema: EnvSchema
    env: Dict[str, str]


@dataclass
class ChainResult:
    steps: List[tuple[str, ValidationResult]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.is_valid for _, r in self.steps)

    @property
    def total_errors(self) -> int:
        return sum(r.error_count for _, r in self.steps)

    @property
    def failed_steps(self) -> List[str]:
        return [name for name, r in self.steps if not r.is_valid]

    def errors_for(self, step_name: str) -> List[ValidationError]:
        for name, result in self.steps:
            if name == step_name:
                return result.errors
        return []

    def __str__(self) -> str:
        lines = [f"ChainResult: {'OK' if self.ok else 'FAILED'} ({len(self.steps)} steps)"]
        for name, result in self.steps:
            status = "OK" if result.is_valid else f"{result.error_count} error(s)"
            lines.append(f"  [{name}] {status}")
        return "\n".join(lines)


def run_chain(steps: List[ChainStep], stop_on_first_failure: bool = False) -> ChainResult:
    """Run a sequence of validation steps and return an aggregated ChainResult."""
    chain_result = ChainResult()
    for step in steps:
        validator = EnvValidator(step.schema)
        result = validator.validate(step.env)
        chain_result.steps.append((step.name, result))
        if stop_on_first_failure and not result.is_valid:
            break
    return chain_result
