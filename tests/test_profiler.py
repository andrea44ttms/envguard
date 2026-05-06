"""Tests for envguard.profiler."""

import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.validator import EnvValidator
from envguard.profiler import profile_env, EnvProfile


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema(name="APP_NAME", type=EnvVarType.STRING, required=True))
    s.add(EnvVarSchema(name="PORT", type=EnvVarType.INTEGER, required=False, default="8080", min_value=1, max_value=65535))
    s.add(EnvVarSchema(name="DEBUG", type=EnvVarType.BOOLEAN, required=False, default="false"))
    s.add(EnvVarSchema(name="API_SECRET", type=EnvVarType.STRING, required=True))
    s.add(EnvVarSchema(name="LOG_LEVEL", type=EnvVarType.STRING, required=False, allowed_values=["DEBUG", "INFO", "WARNING"]))
    return s


def _validate(schema, env):
    return EnvValidator(schema).validate(env)


def test_profile_total_count(schema):
    result = _validate(schema, {"APP_NAME": "myapp", "API_SECRET": "s3cr3t"})
    prof = profile_env(schema, result)
    assert prof.total == 5


def test_profile_required_optional_split(schema):
    result = _validate(schema, {"APP_NAME": "myapp", "API_SECRET": "s3cr3t"})
    prof = profile_env(schema, result)
    assert prof.required_count == 2
    assert prof.optional_count == 3


def test_profile_by_type(schema):
    result = _validate(schema, {"APP_NAME": "myapp", "API_SECRET": "s3cr3t"})
    prof = profile_env(schema, result)
    assert prof.by_type["string"] == 3
    assert prof.by_type["integer"] == 1
    assert prof.by_type["boolean"] == 1


def test_profile_sensitive_keys(schema):
    result = _validate(schema, {"APP_NAME": "myapp", "API_SECRET": "s3cr3t"})
    prof = profile_env(schema, result)
    assert "API_SECRET" in prof.sensitive_keys


def test_profile_with_defaults(schema):
    result = _validate(schema, {"APP_NAME": "myapp", "API_SECRET": "s3cr3t"})
    prof = profile_env(schema, result)
    assert "PORT" in prof.with_defaults
    assert "DEBUG" in prof.with_defaults


def test_profile_with_constraints(schema):
    result = _validate(schema, {"APP_NAME": "myapp", "API_SECRET": "s3cr3t"})
    prof = profile_env(schema, result)
    assert "PORT" in prof.with_constraints
    assert "LOG_LEVEL" in prof.with_constraints


def test_health_score_perfect(schema):
    result = _validate(schema, {"APP_NAME": "myapp", "API_SECRET": "s3cr3t"})
    prof = profile_env(schema, result)
    assert prof.health_score == 1.0


def test_health_score_with_errors(schema):
    result = _validate(schema, {"APP_NAME": "myapp"})  # missing API_SECRET
    prof = profile_env(schema, result)
    assert prof.health_score < 1.0
    assert "API_SECRET" in prof.error_keys


def test_str_output(schema):
    result = _validate(schema, {"APP_NAME": "myapp", "API_SECRET": "s3cr3t"})
    prof = profile_env(schema, result)
    text = str(prof)
    assert "EnvProfile" in text
    assert "health=" in text
