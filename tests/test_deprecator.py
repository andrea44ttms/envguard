"""Tests for envguard.deprecator."""
import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.deprecator import check_deprecations, DeprecationReport


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema(name="APP_HOST", type=EnvVarType.STRING, required=True))
    s.add(
        EnvVarSchema(
            name="OLD_API_KEY",
            type=EnvVarType.STRING,
            required=False,
            metadata={"deprecated": "Use NEW_API_KEY instead."},
        )
    )
    s.add(
        EnvVarSchema(
            name="LEGACY_SECRET",
            type=EnvVarType.STRING,
            required=False,
            metadata={"deprecated": "Rotate to VAULT_SECRET."},
        )
    )
    s.add(EnvVarSchema(name="DB_PORT", type=EnvVarType.INTEGER, required=False))
    return s


def test_no_deprecations_when_env_is_clean(schema):
    env = {"APP_HOST": "localhost", "DB_PORT": "5432"}
    report = check_deprecations(env, schema)
    assert not report.has_warnings
    assert report.count == 0


def test_detects_single_deprecated_key(schema):
    env = {"APP_HOST": "localhost", "OLD_API_KEY": "abc123"}
    report = check_deprecations(env, schema)
    assert report.has_warnings
    assert "OLD_API_KEY" in report.keys()


def test_detects_multiple_deprecated_keys(schema):
    env = {"APP_HOST": "x", "OLD_API_KEY": "a", "LEGACY_SECRET": "s"}
    report = check_deprecations(env, schema)
    assert report.count == 2
    assert set(report.keys()) == {"OLD_API_KEY", "LEGACY_SECRET"}


def test_deprecated_message_is_preserved(schema):
    env = {"OLD_API_KEY": "val"}
    report = check_deprecations(env, schema)
    assert report.warnings[0].message == "Use NEW_API_KEY instead."


def test_sensitive_key_is_redacted_by_default(schema):
    env = {"LEGACY_SECRET": "topsecret"}
    report = check_deprecations(env, schema)
    w = report.warnings[0]
    assert w.redacted is True
    assert w.value is None
    assert "[REDACTED]" in str(w)


def test_sensitive_key_not_redacted_when_disabled(schema):
    env = {"LEGACY_SECRET": "topsecret"}
    report = check_deprecations(env, schema, redact=False)
    w = report.warnings[0]
    assert w.redacted is False
    assert w.value == "topsecret"


def test_non_deprecated_key_not_flagged_even_if_present(schema):
    env = {"APP_HOST": "prod.example.com", "DB_PORT": "5432"}
    report = check_deprecations(env, schema)
    assert report.count == 0


def test_str_no_warnings():
    report = DeprecationReport(warnings=[])
    assert "No deprecated" in str(report)


def test_str_with_warnings(schema):
    env = {"OLD_API_KEY": "abc"}
    report = check_deprecations(env, schema, redact=False)
    output = str(report)
    assert "Deprecated variables" in output
    assert "OLD_API_KEY" in output
    assert "Use NEW_API_KEY instead." in output
