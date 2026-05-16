"""Migrate env vars by applying rename + patch operations in a single pass."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class MigrationStep:
    """A single rename or patch step in a migration plan."""
    action: str          # 'rename' | 'patch'
    key: str
    value: Optional[str] = None   # used for 'patch'
    new_key: Optional[str] = None # used for 'rename'

    def __str__(self) -> str:
        if self.action == "rename":
            return f"rename  {self.key!r} -> {self.new_key!r}"
        return f"patch   {self.key!r} = {self.value!r}"


@dataclass
class MigrationResult:
    """Result of applying a migration plan to an env dict."""
    original: Dict[str, str]
    migrated: Dict[str, str]
    applied: List[MigrationStep] = field(default_factory=list)
    skipped: List[MigrationStep] = field(default_factory=list)

    @property
    def apply_count(self) -> int:
        return len(self.applied)

    @property
    def skip_count(self) -> int:
        return len(self.skipped)

    def __str__(self) -> str:
        lines = [
            f"MigrationResult: {self.apply_count} applied, {self.skip_count} skipped",
        ]
        for step in self.applied:
            lines.append(f"  [applied]  {step}")
        for step in self.skipped:
            lines.append(f"  [skipped]  {step}")
        return "\n".join(lines)


def migrate_env(
    env: Dict[str, str],
    steps: List[MigrationStep],
) -> MigrationResult:
    """Apply *steps* sequentially to *env*, returning a MigrationResult.

    Rename steps that reference a missing key are skipped.
    Patch steps always upsert the key (add or overwrite).
    """
    original = dict(env)
    current: Dict[str, str] = dict(env)
    applied: List[MigrationStep] = []
    skipped: List[MigrationStep] = []

    for step in steps:
        if step.action == "rename":
            if step.key not in current:
                skipped.append(step)
                continue
            if step.new_key is None:
                skipped.append(step)
                continue
            current[step.new_key] = current.pop(step.key)
            applied.append(step)
        elif step.action == "patch":
            current[step.key] = step.value or ""
            applied.append(step)
        else:
            skipped.append(step)

    return MigrationResult(
        original=original,
        migrated=current,
        applied=applied,
        skipped=skipped,
    )
