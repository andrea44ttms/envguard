"""Tests for envguard.deduplicator."""
import pytest

from envguard.deduplicator import DeduplicationResult, DuplicateGroup, deduplicate_env


@pytest.fixture()
def sample_env():
    return {
        "DB_HOST": "localhost",
        "REDIS_HOST": "localhost",  # duplicate of DB_HOST
        "APP_PORT": "8080",
        "METRICS_PORT": "8080",  # duplicate of APP_PORT
        "DEBUG": "true",
    }


def test_no_duplicates_when_all_values_unique():
    env = {"A": "1", "B": "2", "C": "3"}
    result = deduplicate_env(env)
    assert not result.has_duplicates
    assert result.duplicate_count == 0
    assert result.removed_keys == []


def test_detects_duplicate_groups(sample_env):
    result = deduplicate_env(sample_env)
    assert result.has_duplicates
    assert len(result.duplicate_groups) == 2


def test_duplicate_count_reflects_all_involved_keys(sample_env):
    result = deduplicate_env(sample_env)
    # 2 groups × 2 keys each = 4
    assert result.duplicate_count == 4


def test_keep_first_removes_later_duplicates(sample_env):
    result = deduplicate_env(sample_env, keep="first")
    # REDIS_HOST and METRICS_PORT are the second occurrences
    assert "REDIS_HOST" not in result.env
    assert "METRICS_PORT" not in result.env
    # First occurrences are kept
    assert "DB_HOST" in result.env
    assert "APP_PORT" in result.env


def test_keep_none_removes_all_duplicates(sample_env):
    result = deduplicate_env(sample_env, keep="none")
    for key in ("DB_HOST", "REDIS_HOST", "APP_PORT", "METRICS_PORT"):
        assert key not in result.env
    # Unique key survives
    assert "DEBUG" in result.env


def test_removed_keys_populated_on_keep_first(sample_env):
    result = deduplicate_env(sample_env, keep="first")
    assert len(result.removed_keys) == 2
    assert "REDIS_HOST" in result.removed_keys
    assert "METRICS_PORT" in result.removed_keys


def test_removed_keys_populated_on_keep_none(sample_env):
    result = deduplicate_env(sample_env, keep="none")
    assert len(result.removed_keys) == 4


def test_ignore_keys_excluded_from_detection(sample_env):
    result = deduplicate_env(sample_env, ignore_keys={"REDIS_HOST", "METRICS_PORT"})
    # With those ignored, no duplicate groups should form
    assert not result.has_duplicates


def test_original_env_not_mutated(sample_env):
    original = dict(sample_env)
    deduplicate_env(sample_env, keep="none")
    assert sample_env == original


def test_str_no_duplicates():
    env = {"X": "1"}
    result = deduplicate_env(env)
    assert "No duplicate" in str(result)


def test_str_with_duplicates(sample_env):
    result = deduplicate_env(sample_env)
    output = str(result)
    assert "Duplicate groups" in output


def test_duplicate_group_str():
    group = DuplicateGroup(value="localhost", keys=["DB_HOST", "REDIS_HOST"])
    text = str(group)
    assert "DB_HOST" in text
    assert "REDIS_HOST" in text
    assert "localhost" in text
