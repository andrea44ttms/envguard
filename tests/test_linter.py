"""Tests for envguard.linter."""
from __future__ import annotations

import pytest

from envguard.linter import LintIssue, LintResult, lint_env
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema("APP_ENV", EnvVarType.STRING, required=True))
    s.add(EnvVarSchema("PORT", EnvVarType.INTEGER, required=True))
    s.add(EnvVarSchema("DEBUG", EnvVarType.BOOLEAN, required=False, default="false"))
    return s


def test_clean_env_has_no_issues(schema):
    env = {"APP_ENV": "production", "PORT": "8080", "DEBUG": "false"}
    result = lint_env(env, schema)
    assert not result.has_issues
    assert result.error_count == 0
    assert result.warning_count == 0


def test_undeclared_key_is_warning(schema):
    env = {"APP_ENV": "dev", "PORT": "8080", "UNKNOWN_VAR": "oops"}
    result = lint_env(env, schema)
    keys = [i.key for i in result.issues]
    assert "UNKNOWN_VAR" in keys
    issue = next(i for i in result.issues if i.key == "UNKNOWN_VAR")
    assert issue.severity == "warning"


def test_whitespace_in_value_is_warning(schema):
    env = {"APP_ENV": "  dev  ", "PORT": "8080"}
    result = lint_env(env, schema)
    assert any(i.key == "APP_ENV" and "whitespace" in i.message for i in result.issues)


def test_empty_value_is_warning(schema):
    env = {"APP_ENV": "", "PORT": "8080"}
    result = lint_env(env, schema)
    assert any(i.key == "APP_ENV" and "empty" in i.message for i in result.issues)


def test_lowercase_key_is_warning():
    s = EnvSchema()
    s.add(EnvVarSchema("app_env", EnvVarType.STRING, required=True))
    result = lint_env({"app_env": "dev"}, s)
    assert any(i.key == "app_env" and "uppercase" in i.message for i in result.issues)


def test_required_with_default_is_warning():
    s = EnvSchema()
    s.add(EnvVarSchema("PORT", EnvVarType.INTEGER, required=True, default="8080"))
    result = lint_env({"PORT": "8080"}, s)
    assert any(i.key == "PORT" and "default" in i.message for i in result.issues)


def test_lint_result_str_no_issues():
    result = LintResult()
    assert "No lint issues" in str(result)


def test_lint_result_str_with_issues():
    result = LintResult(
        issues=[
            LintIssue("FOO", "some warning", "warning"),
            LintIssue("BAR", "some error", "error"),
        ]
    )
    text = str(result)
    assert "1 error" in text
    assert "1 warning" in text


def test_lint_issue_str():
    issue = LintIssue("KEY", "bad value", "error")
    assert "[ERROR]" in str(issue)
    assert "KEY" in str(issue)
