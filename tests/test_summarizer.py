"""Tests for envguard.summarizer."""

import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.result import ValidationResult, ValidationError
from envguard.summarizer import summarize_env, EnvSummary


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema("DB_HOST", EnvVarType.STRING, required=True))
    s.add(EnvVarSchema("DB_PORT", EnvVarType.INTEGER, required=True))
    s.add(EnvVarSchema("DEBUG", EnvVarType.BOOLEAN, required=False, default="false"))
    s.add(EnvVarSchema("TIMEOUT", EnvVarType.FLOAT, required=False))
    return s


def _ok_result() -> ValidationResult:
    return ValidationResult(errors=[])


def _err_result(*msgs) -> ValidationResult:
    errors = [ValidationError(key=m.split()[0], message=m) for m in msgs]
    return ValidationResult(errors=errors)


def test_summary_total_count(schema):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "DEBUG": "true", "TIMEOUT": "30.0"}
    summary = summarize_env(schema, _ok_result(), env)
    assert summary.total_vars == 4


def test_summary_required_optional_split(schema):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    summary = summarize_env(schema, _ok_result(), env)
    assert summary.required_count == 2
    assert summary.optional_count == 2


def test_summary_present_count(schema):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    summary = summarize_env(schema, _ok_result(), env)
    assert summary.present_count == 2


def test_summary_missing_required(schema):
    env = {"DB_HOST": "localhost"}  # DB_PORT missing
    summary = summarize_env(schema, _ok_result(), env)
    assert "DB_PORT" in summary.missing_required
    assert summary.missing_required_count == 1


def test_summary_no_missing_required_when_all_present(schema):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    summary = summarize_env(schema, _ok_result(), env)
    assert summary.missing_required == []


def test_summary_coverage_pct_full(schema):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "DEBUG": "true", "TIMEOUT": "1.5"}
    summary = summarize_env(schema, _ok_result(), env)
    assert summary.coverage_pct == 100.0


def test_summary_coverage_pct_partial(schema):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}  # 2 of 4
    summary = summarize_env(schema, _ok_result(), env)
    assert summary.coverage_pct == 50.0


def test_summary_is_valid_true(schema):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    summary = summarize_env(schema, _ok_result(), env)
    assert summary.is_valid is True


def test_summary_is_valid_false(schema):
    env = {"DB_HOST": "localhost"}
    result = _err_result("DB_PORT is required")
    summary = summarize_env(schema, result, env)
    assert summary.is_valid is False
    assert len(summary.error_messages) == 1


def test_summary_type_breakdown(schema):
    env = {}
    summary = summarize_env(schema, _ok_result(), env)
    assert summary.type_breakdown["string"] == 1
    assert summary.type_breakdown["integer"] == 1
    assert summary.type_breakdown["boolean"] == 1
    assert summary.type_breakdown["float"] == 1


def test_summary_str_contains_key_info(schema):
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    summary = summarize_env(schema, _ok_result(), env)
    text = str(summary)
    assert "Total declared" in text
    assert "Coverage" in text
    assert "Valid" in text
