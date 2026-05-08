"""Tests for envguard.comparator."""

import pytest
from envguard.comparator import compare_envs, EnvComparison
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema("SECRET_KEY", EnvVarType.STRING, required=True))
    s.add(EnvVarSchema("PORT", EnvVarType.INTEGER, required=False))
    return s


def test_identical_envs_have_no_differences():
    env = {"PORT": "8000", "DEBUG": "true"}
    result = compare_envs(env, env.copy())
    assert not result.has_differences
    assert set(result.common) == {"PORT", "DEBUG"}


def test_detects_key_only_in_left():
    left = {"PORT": "8000", "EXTRA": "yes"}
    right = {"PORT": "8000"}
    result = compare_envs(left, right)
    assert "EXTRA" in result.only_in_left
    assert not result.only_in_right
    assert result.has_differences


def test_detects_key_only_in_right():
    left = {"PORT": "8000"}
    right = {"PORT": "8000", "NEW_VAR": "hello"}
    result = compare_envs(left, right)
    assert "NEW_VAR" in result.only_in_right
    assert not result.only_in_left


def test_detects_changed_value():
    left = {"PORT": "8000"}
    right = {"PORT": "9000"}
    result = compare_envs(left, right)
    assert "PORT" in result.changed
    assert result.changed["PORT"] == ("8000", "9000")


def test_redacts_sensitive_values_when_schema_provided(schema):
    left = {"SECRET_KEY": "abc123", "PORT": "8000"}
    right = {"SECRET_KEY": "xyz789", "PORT": "8000"}
    result = compare_envs(left, right, schema=schema)
    lv, rv = result.changed["SECRET_KEY"]
    assert "abc123" not in lv
    assert "xyz789" not in rv


def test_no_redaction_without_schema():
    left = {"SECRET_KEY": "abc123"}
    right = {"SECRET_KEY": "xyz789"}
    result = compare_envs(left, right, schema=None)
    lv, rv = result.changed["SECRET_KEY"]
    assert lv == "abc123"
    assert rv == "xyz789"


def test_summary_string_contains_counts():
    left = {"A": "1", "B": "2"}
    right = {"B": "99", "C": "3"}
    result = compare_envs(left, right)
    summary = result.summary()
    assert "Only in left" in summary
    assert "Only in right" in summary
    assert "Changed" in summary


def test_str_representation_lists_keys():
    left = {"ALPHA": "old"}
    right = {"ALPHA": "new", "BETA": "added"}
    result = compare_envs(left, right)
    text = str(result)
    assert "ALPHA" in text
    assert "BETA" in text


def test_empty_envs_produce_empty_comparison():
    result = compare_envs({}, {})
    assert not result.has_differences
    assert result.common == []
