"""Tests for envguard.trimmer."""

import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.trimmer import TrimResult, trim_env


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema(name="APP_HOST", type=EnvVarType.STRING))
    s.add(EnvVarSchema(name="APP_PORT", type=EnvVarType.INTEGER))
    s.add(EnvVarSchema(name="DEBUG", type=EnvVarType.BOOLEAN, required=False))
    return s


@pytest.fixture()
def base_env() -> dict:
    return {
        "APP_HOST": "localhost",
        "APP_PORT": "8080",
        "DEBUG": "true",
        "LEGACY_FLAG": "yes",
        "UNUSED_KEY": "foo",
    }


def test_trim_removes_undeclared_keys(schema, base_env):
    result = trim_env(base_env, schema)
    assert "LEGACY_FLAG" not in result.trimmed
    assert "UNUSED_KEY" not in result.trimmed


def test_trim_keeps_declared_keys(schema, base_env):
    result = trim_env(base_env, schema)
    assert "APP_HOST" in result.trimmed
    assert "APP_PORT" in result.trimmed
    assert "DEBUG" in result.trimmed


def test_remove_count_matches_removed_keys(schema, base_env):
    result = trim_env(base_env, schema)
    assert result.remove_count == 2
    assert set(result.removed_keys) == {"LEGACY_FLAG", "UNUSED_KEY"}


def test_original_is_not_mutated(schema, base_env):
    original_copy = dict(base_env)
    trim_env(base_env, schema)
    assert base_env == original_copy


def test_no_removal_when_all_declared(schema):
    env = {"APP_HOST": "localhost", "APP_PORT": "8080", "DEBUG": "false"}
    result = trim_env(env, schema)
    assert result.remove_count == 0
    assert result.trimmed == env


def test_remove_empty_values(schema):
    env = {"APP_HOST": "localhost", "APP_PORT": "", "DEBUG": ""}
    result = trim_env(env, schema, remove_empty=True)
    assert "APP_PORT" not in result.trimmed
    assert "DEBUG" not in result.trimmed
    assert "APP_HOST" in result.trimmed


def test_remove_empty_false_keeps_empty_values(schema):
    env = {"APP_HOST": "", "APP_PORT": ""}
    result = trim_env(env, schema, remove_empty=False)
    assert "APP_HOST" in result.trimmed
    assert "APP_PORT" in result.trimmed


def test_disable_remove_undeclared_keeps_extra_keys(schema, base_env):
    result = trim_env(base_env, schema, remove_undeclared=False)
    assert "LEGACY_FLAG" in result.trimmed
    assert "UNUSED_KEY" in result.trimmed
    assert result.remove_count == 0


def test_str_output_lists_removed_keys(schema, base_env):
    result = trim_env(base_env, schema)
    text = str(result)
    assert "LEGACY_FLAG" in text
    assert "UNUSED_KEY" in text


def test_str_output_nothing_removed_message(schema):
    env = {"APP_HOST": "h", "APP_PORT": "80"}
    result = trim_env(env, schema)
    assert "(nothing removed)" in str(result)
