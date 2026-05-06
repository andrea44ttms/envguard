"""High-level pipeline: load → merge → validate → audit in one call."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envguard.loader import load_env_file
from envguard.merger import MergeSource, MergeResult, merge_envs
from envguard.schema import EnvSchema
from envguard.validator import EnvValidator
from envguard.result import ValidationResult
from envguard.audit import AuditReport, audit_env


@dataclass
class PipelineResult:
    """Combined result from the full envguard pipeline."""

    merge_result: MergeResult
    validation_result: ValidationResult
    audit_report: AuditReport

    @property
    def ok(self) -> bool:
        """True only when validation passes and there are no undeclared vars."""
        return (
            self.validation_result.is_valid
            and len(self.audit_report.undeclared_vars) == 0
        )

    def summary(self) -> str:
        lines = []
        status = "PASS" if self.ok else "FAIL"
        lines.append(f"[envguard] Pipeline status: {status}")
        lines.append(
            f"  Validation errors : {self.validation_result.error_count}"
        )
        lines.append(
            f"  Undeclared vars   : {len(self.audit_report.undeclared_vars)}"
        )
        lines.append(
            f"  Merge conflicts   : {self.merge_result.conflict_count}"
        )
        return "\n".join(lines)


def run_pipeline(
    schema: EnvSchema,
    *,
    env_files: Optional[List[str]] = None,
    extra_env: Optional[Dict[str, str]] = None,
    os_environ: Optional[Dict[str, str]] = None,
) -> PipelineResult:
    """Load, merge, validate and audit env vars according to *schema*.

    Priority (lowest → highest):
      1. env_files (in list order, later files get higher priority)
      2. extra_env
      3. os_environ
    """
    sources: List[MergeSource] = []

    for idx, path in enumerate(env_files or []):
        env = load_env_file(path)
        sources.append(MergeSource(name=path, env=env, priority=idx))

    base_priority = len(sources)

    if extra_env:
        sources.append(
            MergeSource(name="extra_env", env=extra_env, priority=base_priority)
        )

    if os_environ:
        sources.append(
            MergeSource(name="os_environ", env=os_environ, priority=base_priority + 1)
        )

    merge_result = merge_envs(*sources) if sources else MergeResult()

    validator = EnvValidator(schema)
    validation_result = validator.validate(merge_result.merged)

    audit_report = audit_env(merge_result.merged, schema)

    return PipelineResult(
        merge_result=merge_result,
        validation_result=validation_result,
        audit_report=audit_report,
    )
