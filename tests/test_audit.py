"""Tests for envguard.audit module."""

import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.audit import audit_env, _is_sensitive, AuditReport


@pytest.fixture()
def schema():
    s = EnvSchema()
    s.add("DATABASE_URL", EnvVarSchema(type=EnvVarType.STRING, required=True))
    s.add("PORT", EnvVarSchema(type=EnvVarType.INTEGER, required=True))
    s.add("API_SECRET", EnvVarSchema(type=EnvVarType.STRING, required=False))
    return s


def test_no_undeclared_vars(schema):
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432", "API_SECRET": "abc"}
    report = audit_env(schema, env)
    assert report.undeclared == []


def test_detects_undeclared_vars(schema):
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432", "EXTRA_VAR": "oops"}
    report = audit_env(schema, env)
    assert "EXTRA_VAR" in report.undeclared


def test_redacts_sensitive_values(schema):
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432", "API_SECRET": "supersecret"}
    report = audit_env(schema, env)
    assert report.redacted_snapshot["API_SECRET"] == "***REDACTED***"
    assert report.redacted_snapshot["PORT"] == "5432"


def test_undeclared_vars_excluded_from_snapshot(schema):
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432", "UNKNOWN": "val"}
    report = audit_env(schema, env)
    assert "UNKNOWN" not in report.redacted_snapshot


@pytest.mark.parametrize("name,expected", [
    ("DB_PASSWORD", True),
    ("SECRET_KEY", True),
    ("AUTH_TOKEN", True),
    ("API_KEY", True),
    ("HOST", False),
    ("PORT", False),
    ("DEBUG", False),
])
def test_is_sensitive(name, expected):
    assert _is_sensitive(name) is expected


def test_audit_report_str(schema):
    env = {"DATABASE_URL": "postgres://localhost/db", "PORT": "5432", "ROGUE": "x"}
    report = audit_env(schema, env)
    text = str(report)
    assert "ROGUE" in text
    assert "Undeclared" in text
