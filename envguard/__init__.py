"""envguard — Lightweight utility to validate and audit .env files."""
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.validator import EnvValidator
from envguard.result import ValidationResult, ValidationError
from envguard.loader import load_env_file
from envguard.reporter import render_report, ReportFormat
from envguard.audit import audit_env, AuditReport
from envguard.exporter import export_to_dict, export_to_os_environ, export_to_dotenv
from envguard.differ import EnvDiff
from envguard.merger import MergeResult
from envguard.snapshot import take_snapshot, EnvSnapshot
from envguard.profiler import profile_env, EnvProfile
from envguard.redactor import redact_env, is_sensitive
from envguard.formatter import FormattedEnv
from envguard.comparator import compare_envs, EnvComparison
from envguard.normalizer import normalize_env, NormalizeResult
from envguard.masker import MaskResult
from envguard.linter import lint_env, LintResult
from envguard.templater import generate_template, TemplateResult
from envguard.scorer import score_env, EnvScore
from envguard.grouper import group_by_prefix, group_by_categories, GroupResult

__all__ = [
    "EnvSchema", "EnvVarSchema", "EnvVarType",
    "EnvValidator", "ValidationResult", "ValidationError",
    "load_env_file", "render_report", "ReportFormat",
    "audit_env", "AuditReport",
    "export_to_dict", "export_to_os_environ", "export_to_dotenv",
    "EnvDiff", "MergeResult", "take_snapshot", "EnvSnapshot",
    "profile_env", "EnvProfile", "redact_env", "is_sensitive",
    "FormattedEnv", "compare_envs", "EnvComparison",
    "normalize_env", "NormalizeResult", "MaskResult",
    "lint_env", "LintResult", "generate_template", "TemplateResult",
    "score_env", "EnvScore",
    "group_by_prefix", "group_by_categories", "GroupResult",
]
