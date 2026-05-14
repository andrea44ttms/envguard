"""Tests for envguard.splitter."""
from __future__ import annotations

import pytest

from envguard.splitter import SplitResult, split_env


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "REDIS_TTL": "300",
        "APP_DEBUG": "true",
        "LOG_LEVEL": "info",
    }


def test_split_by_prefix_creates_buckets(sample_env):
    result = split_env(sample_env, prefixes=["DB_", "REDIS_"])
    assert "DB_" in result.bucket_names
    assert "REDIS_" in result.bucket_names


def test_strip_prefix_removes_prefix_from_keys(sample_env):
    result = split_env(sample_env, prefixes=["DB_"], strip_prefix=True)
    assert "HOST" in result.get("DB_")
    assert "PORT" in result.get("DB_")


def test_no_strip_prefix_keeps_full_key(sample_env):
    result = split_env(sample_env, prefixes=["DB_"], strip_prefix=False)
    assert "DB_HOST" in result.get("DB_")
    assert "DB_PORT" in result.get("DB_")


def test_unmatched_keys_collected(sample_env):
    result = split_env(sample_env, prefixes=["DB_", "REDIS_"])
    assert "APP_DEBUG" in result.unmatched
    assert "LOG_LEVEL" in result.unmatched


def test_unmatched_count(sample_env):
    result = split_env(sample_env, prefixes=["DB_", "REDIS_"])
    assert result.unmatched_count == 2


def test_total_matched(sample_env):
    result = split_env(sample_env, prefixes=["DB_", "REDIS_"])
    assert result.total_matched == 4


def test_explicit_mapping_wins_over_prefix(sample_env):
    result = split_env(
        sample_env,
        prefixes=["DB_"],
        mapping={"DB_HOST": "overrides"},
    )
    assert "DB_HOST" in result.get("overrides")
    # DB_HOST should NOT also appear in the DB_ bucket
    assert "HOST" not in result.get("DB_")


def test_longest_prefix_wins():
    env = {"DB_PRIMARY_HOST": "primary", "DB_HOST": "fallback"}
    result = split_env(env, prefixes=["DB_", "DB_PRIMARY_"], strip_prefix=True)
    assert "HOST" in result.get("DB_PRIMARY_")
    assert "HOST" in result.get("DB_")


def test_empty_env_returns_empty_result():
    result = split_env({}, prefixes=["DB_"])
    assert result.total_matched == 0
    assert result.unmatched_count == 0


def test_no_prefixes_all_unmatched(sample_env):
    result = split_env(sample_env)
    assert result.total_matched == 0
    assert result.unmatched_count == len(sample_env)


def test_get_missing_bucket_returns_empty(sample_env):
    result = split_env(sample_env, prefixes=["DB_"])
    assert result.get("NONEXISTENT") == {}


def test_bucket_names_property(sample_env):
    result = split_env(sample_env, prefixes=["DB_", "REDIS_"])
    names = result.bucket_names
    assert "DB_" in names
    assert "REDIS_" in names
