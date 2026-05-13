"""Tests for envguard.cloner."""
import pytest
from envguard.cloner import clone_env, CloneResult


@pytest.fixture()
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_ENV": "production",
        "APP_DEBUG": "false",
        "SECRET_KEY": "abc123",
    }


def test_clone_all_when_no_selector(sample_env):
    result = clone_env(sample_env)
    assert result.clone_count == len(sample_env)
    assert result.skip_count == 0
    assert result.cloned == sample_env


def test_clone_by_explicit_keys(sample_env):
    result = clone_env(sample_env, keys=["DB_HOST", "SECRET_KEY"])
    assert set(result.cloned.keys()) == {"DB_HOST", "SECRET_KEY"}
    assert result.skip_count == 3


def test_clone_missing_explicit_key_is_ignored(sample_env):
    result = clone_env(sample_env, keys=["DB_HOST", "NONEXISTENT"])
    assert "DB_HOST" in result.cloned
    assert "NONEXISTENT" not in result.cloned
    assert result.clone_count == 1


def test_clone_by_glob_pattern(sample_env):
    result = clone_env(sample_env, pattern="DB_*")
    assert set(result.cloned.keys()) == {"DB_HOST", "DB_PORT"}
    assert result.skip_count == 3


def test_clone_by_prefix(sample_env):
    result = clone_env(sample_env, prefix="APP_")
    assert set(result.cloned.keys()) == {"APP_ENV", "APP_DEBUG"}


def test_clone_by_prefix_strip(sample_env):
    result = clone_env(sample_env, prefix="APP_", strip_prefix=True)
    assert set(result.cloned.keys()) == {"ENV", "DEBUG"}
    assert result.cloned["ENV"] == "production"


def test_strip_prefix_without_prefix_flag_leaves_keys_unchanged(sample_env):
    # strip_prefix=True without prefix provided — no stripping expected
    result = clone_env(sample_env, strip_prefix=True)
    assert set(result.cloned.keys()) == set(sample_env.keys())


def test_keys_takes_priority_over_pattern(sample_env):
    result = clone_env(sample_env, keys=["SECRET_KEY"], pattern="DB_*")
    assert set(result.cloned.keys()) == {"SECRET_KEY"}


def test_source_size_is_recorded(sample_env):
    result = clone_env(sample_env, prefix="DB_")
    assert result.source_size == len(sample_env)


def test_str_output_contains_counts(sample_env):
    result = clone_env(sample_env, prefix="DB_")
    text = str(result)
    assert "CloneResult" in text
    assert "cloned" in text
    assert "skipped" in text


def test_empty_env_returns_empty_result():
    result = clone_env({}, pattern="DB_*")
    assert result.clone_count == 0
    assert result.skip_count == 0
    assert result.source_size == 0
