"""Tests for envguard.flattener."""
import pytest
from envguard.flattener import FlattenResult, flatten_env


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb",
        "REDIS_HOST": "127.0.0.1",
        "REDIS_PORT": "6379",
        "APP_ENV": "production",
        "DEBUG": "false",
    }


def test_flatten_with_explicit_prefixes(sample_env):
    result = flatten_env(sample_env, prefixes=["DB", "REDIS"])
    assert isinstance(result, FlattenResult)
    assert "DB" in result.groups
    assert "REDIS" in result.groups


def test_db_group_contains_correct_keys(sample_env):
    result = flatten_env(sample_env, prefixes=["DB"])
    db = result.get_group("DB")
    assert set(db.keys()) == {"HOST", "PORT", "NAME"}


def test_redis_group_values(sample_env):
    result = flatten_env(sample_env, prefixes=["REDIS"])
    redis = result.get_group("REDIS")
    assert redis["HOST"] == "127.0.0.1"
    assert redis["PORT"] == "6379"


def test_ungrouped_contains_unmatched_keys(sample_env):
    result = flatten_env(sample_env, prefixes=["DB", "REDIS"])
    assert "APP_ENV" in result.ungrouped
    assert "DEBUG" in result.ungrouped


def test_total_count_equals_env_size(sample_env):
    result = flatten_env(sample_env, prefixes=["DB", "REDIS"])
    assert result.total_count == len(sample_env)


def test_group_names_sorted(sample_env):
    result = flatten_env(sample_env, prefixes=["REDIS", "DB"])
    assert result.group_names == ["DB", "REDIS"]


def test_auto_detect_prefixes(sample_env):
    result = flatten_env(sample_env, prefixes=None)
    # All keys with underscores should be grouped
    assert "DB" in result.groups
    assert "REDIS" in result.groups
    assert "APP" in result.groups


def test_strip_prefix_false_keeps_full_key(sample_env):
    result = flatten_env(sample_env, prefixes=["DB"], strip_prefix=False)
    db = result.get_group("DB")
    assert "DB_HOST" in db
    assert "DB_PORT" in db


def test_get_group_unknown_prefix_returns_empty(sample_env):
    result = flatten_env(sample_env, prefixes=["DB"])
    assert result.get_group("UNKNOWN") == {}


def test_empty_env_returns_empty_result():
    result = flatten_env({}, prefixes=["DB"])
    assert result.total_count == 0
    assert result.groups == {}
    assert result.ungrouped == {}


def test_case_insensitive_prefix_matching():
    env = {"db_host": "localhost", "db_port": "5432"}
    result = flatten_env(env, prefixes=["DB"], separator="_")
    db = result.get_group("DB")
    assert "host" in db or "HOST" in db  # sub-key retains original casing


def test_no_prefixes_all_ungrouped():
    env = {"FOO": "1", "BAR": "2"}
    result = flatten_env(env, prefixes=[])
    assert result.ungrouped == env
    assert result.groups == {}
