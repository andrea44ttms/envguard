"""Tests for envguard.differ module."""

import pytest
from envguard.differ import diff_envs, EnvDiff


@pytest.fixture
def base_env():
    return {
        "APP_NAME": "myapp",
        "DEBUG": "false",
        "DB_PASSWORD": "secret123",
        "PORT": "8080",
        "REMOVED_VAR": "gone",
    }


@pytest.fixture
def target_env():
    return {
        "APP_NAME": "myapp",
        "DEBUG": "true",
        "DB_PASSWORD": "newpassword",
        "PORT": "8080",
        "NEW_VAR": "hello",
    }


def test_no_changes_when_envs_identical():
    env = {"FOO": "bar", "BAZ": "qux"}
    diff = diff_envs(env, env.copy())
    assert not diff.has_changes
    assert diff.unchanged == ["BAZ", "FOO"]


def test_detects_added_keys(base_env, target_env):
    diff = diff_envs(base_env, target_env)
    assert "NEW_VAR" in diff.added
    assert diff.added["NEW_VAR"] == "hello"


def test_detects_removed_keys(base_env, target_env):
    diff = diff_envs(base_env, target_env)
    assert "REMOVED_VAR" in diff.removed


def test_detects_changed_keys(base_env, target_env):
    diff = diff_envs(base_env, target_env)
    assert "DEBUG" in diff.changed
    old, new = diff.changed["DEBUG"]
    assert old == "false"
    assert new == "true"


def test_unchanged_keys_not_in_diff(base_env, target_env):
    diff = diff_envs(base_env, target_env)
    assert "APP_NAME" in diff.unchanged
    assert "PORT" in diff.unchanged


def test_sensitive_values_redacted(base_env, target_env):
    diff = diff_envs(base_env, target_env, redact_sensitive=True)
    assert diff.changed["DB_PASSWORD"] == ("***", "***")
    assert diff.removed["REMOVED_VAR"] == "gone"  # not sensitive


def test_sensitive_values_not_redacted_when_disabled(base_env, target_env):
    diff = diff_envs(base_env, target_env, redact_sensitive=False)
    old, new = diff.changed["DB_PASSWORD"]
    assert old == "secret123"
    assert new == "newpassword"


def test_has_changes_true_when_diff_exists(base_env, target_env):
    diff = diff_envs(base_env, target_env)
    assert diff.has_changes is True


def test_summary_no_changes():
    env = {"X": "1"}
    diff = diff_envs(env, env.copy())
    assert diff.summary() == "No differences found."


def test_summary_with_changes(base_env, target_env):
    diff = diff_envs(base_env, target_env)
    summary = diff.summary()
    assert "Added" in summary
    assert "Removed" in summary
    assert "Changed" in summary


def test_str_representation(base_env, target_env):
    diff = diff_envs(base_env, target_env, redact_sensitive=False)
    text = str(diff)
    assert "+" in text  # added
    assert "-" in text  # removed
    assert "~" in text  # changed
