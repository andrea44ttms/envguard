"""Tests for envguard.scorer."""

from __future__ import annotations

import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.validator import EnvValidator
from envguard.scorer import score_env, EnvScore


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema("APP_ENV", EnvVarType.STRING, required=True))
    s.add(EnvVarSchema("PORT", EnvVarType.INTEGER, required=True, min_value=1, max_value=65535))
    s.add(EnvVarSchema("DEBUG", EnvVarType.BOOLEAN, required=False, default="false"))
    s.add(EnvVarSchema("MAX_RETRIES", EnvVarType.INTEGER, required=False, default="3"))
    return s


def _validate(env, schema):
    return EnvValidator(schema).validate(env)


def test_perfect_env_scores_100(schema):
    env = {"APP_ENV": "production", "PORT": "8080", "DEBUG": "false", "MAX_RETRIES": "3"}
    result = _validate(env, schema)
    score = score_env(env, schema, result)
    assert score.score == 100.0


def test_missing_optional_reduces_completeness(schema):
    env = {"APP_ENV": "production", "PORT": "8080"}
    result = _validate(env, schema)
    score = score_env(env, schema, result)
    assert score.completeness < 1.0
    assert score.required_coverage == 1.0


def test_missing_required_reduces_required_coverage(schema):
    env = {"APP_ENV": "production"}  # PORT missing
    result = _validate(env, schema)
    score = score_env(env, schema, result)
    assert score.required_coverage < 1.0
    assert score.score < 100.0


def test_type_error_penalises_score(schema):
    env = {"APP_ENV": "production", "PORT": "not_a_number", "DEBUG": "false", "MAX_RETRIES": "3"}
    result = _validate(env, schema)
    score = score_env(env, schema, result)
    assert score.type_errors >= 1
    assert score.score < 100.0


def test_constraint_error_penalises_score(schema):
    env = {"APP_ENV": "production", "PORT": "99999", "DEBUG": "false", "MAX_RETRIES": "3"}
    result = _validate(env, schema)
    score = score_env(env, schema, result)
    assert score.constraint_errors >= 1
    assert score.score < 100.0


def test_score_clamped_between_0_and_100(schema):
    env = {}  # everything missing
    result = _validate(env, schema)
    score = score_env(env, schema, result)
    assert 0.0 <= score.score <= 100.0


def test_total_and_present_counts(schema):
    env = {"APP_ENV": "staging", "PORT": "5000"}
    result = _validate(env, schema)
    score = score_env(env, schema, result)
    assert score.total == 4
    assert score.present == 2


def test_breakdown_keys_present(schema):
    env = {"APP_ENV": "dev", "PORT": "3000", "DEBUG": "true", "MAX_RETRIES": "5"}
    result = _validate(env, schema)
    score = score_env(env, schema, result)
    assert "completeness" in score.breakdown
    assert "required_coverage" in score.breakdown


def test_empty_schema_scores_100():
    empty_schema = EnvSchema()
    result = EnvValidator(empty_schema).validate({})
    score = score_env({}, empty_schema, result)
    assert score.score == 100.0
    assert score.completeness == 1.0
    assert score.required_coverage == 1.0
