"""Tests for envguard.merger module."""

import pytest
from envguard.merger import MergeSource, MergeResult, merge_envs


@pytest.fixture
def base_source() -> MergeSource:
    return MergeSource(
        name="base",
        env={"HOST": "localhost", "PORT": "5432", "DEBUG": "false"},
        priority=0,
    )


@pytest.fixture
def override_source() -> MergeSource:
    return MergeSource(
        name="override",
        env={"PORT": "9999", "SECRET": "abc123"},
        priority=10,
    )


def test_single_source_passthrough(base_source):
    result = merge_envs(base_source)
    assert result.merged == base_source.env
    assert result.conflict_count == 0


def test_higher_priority_wins(base_source, override_source):
    result = merge_envs(base_source, override_source)
    assert result.merged["PORT"] == "9999"
    assert result.origin_of("PORT") == "override"


def test_lower_priority_does_not_overwrite(base_source, override_source):
    result = merge_envs(override_source, base_source)  # order shouldn't matter
    assert result.merged["PORT"] == "9999"


def test_non_conflicting_keys_merged(base_source, override_source):
    result = merge_envs(base_source, override_source)
    assert "HOST" in result.merged
    assert "SECRET" in result.merged
    assert result.merged["HOST"] == "localhost"


def test_conflict_detected(base_source, override_source):
    result = merge_envs(base_source, override_source)
    conflict_keys = [k for k, _ in result.conflicts]
    assert "PORT" in conflict_keys


def test_no_conflict_when_unique_keys():
    s1 = MergeSource(name="s1", env={"A": "1"}, priority=0)
    s2 = MergeSource(name="s2", env={"B": "2"}, priority=1)
    result = merge_envs(s1, s2)
    assert result.conflict_count == 0
    assert result.merged == {"A": "1", "B": "2"}


def test_origin_of_returns_none_for_missing_key(base_source):
    result = merge_envs(base_source)
    assert result.origin_of("NONEXISTENT") is None


def test_str_output_contains_conflict_info(base_source, override_source):
    result = merge_envs(base_source, override_source)
    text = str(result)
    assert "PORT" in text
    assert "override" in text


def test_three_way_merge_highest_priority_wins():
    s1 = MergeSource(name="defaults", env={"X": "1", "Y": "a"}, priority=0)
    s2 = MergeSource(name="env_file", env={"X": "2"}, priority=5)
    s3 = MergeSource(name="os_env", env={"X": "3"}, priority=10)
    result = merge_envs(s1, s2, s3)
    assert result.merged["X"] == "3"
    assert result.origin_of("X") == "os_env"
    assert result.merged["Y"] == "a"
