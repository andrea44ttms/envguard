"""Tests for envguard.filter."""
from __future__ import annotations

import pytest

from envguard.filter import FilterResult, filter_env
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "APP_DEBUG": "true",
        "APP_PORT": "8080",
    }


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add("DB_HOST", EnvVarSchema(type=EnvVarType.STRING))
    s.add("DB_PORT", EnvVarSchema(type=EnvVarType.INTEGER))
    s.add("REDIS_URL", EnvVarSchema(type=EnvVarType.STRING))
    s.add("APP_DEBUG", EnvVarSchema(type=EnvVarType.BOOLEAN))
    s.add("APP_PORT", EnvVarSchema(type=EnvVarType.INTEGER))
    return s


def test_no_criteria_matches_all(sample_env):
    result = filter_env(sample_env)
    assert result.match_count == len(sample_env)
    assert result.excluded_count == 0


def test_pattern_filters_by_prefix(sample_env):
    result = filter_env(sample_env, patterns=["DB_*"])
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT"}


def test_multiple_patterns_union(sample_env):
    result = filter_env(sample_env, patterns=["DB_*", "REDIS_*"])
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT", "REDIS_URL"}


def test_excluded_keys_not_in_matched(sample_env):
    result = filter_env(sample_env, patterns=["APP_*"])
    for key in result.excluded:
        assert key not in result.matched


def test_filter_by_type_integer(sample_env, schema):
    result = filter_env(sample_env, var_type=EnvVarType.INTEGER, schema=schema)
    assert set(result.matched.keys()) == {"DB_PORT", "APP_PORT"}


def test_filter_by_type_boolean(sample_env, schema):
    result = filter_env(sample_env, var_type=EnvVarType.BOOLEAN, schema=schema)
    assert set(result.matched.keys()) == {"APP_DEBUG"}


def test_var_type_without_schema_matches_all(sample_env):
    # type_keys stays None when schema is absent — no type filtering applied
    result = filter_env(sample_env, var_type=EnvVarType.INTEGER, schema=None)
    assert result.match_count == len(sample_env)


def test_predicate_filter(sample_env):
    result = filter_env(sample_env, predicate=lambda k, v: v.isdigit())
    assert set(result.matched.keys()) == {"DB_PORT", "APP_PORT"}


def test_combined_pattern_and_predicate(sample_env):
    result = filter_env(
        sample_env,
        patterns=["APP_*"],
        predicate=lambda k, v: v.isdigit(),
    )
    assert set(result.matched.keys()) == {"APP_PORT"}


def test_filter_name_stored(sample_env):
    result = filter_env(sample_env, filter_name="my-filter")
    assert result.filter_name == "my-filter"


def test_str_output_contains_filter_name(sample_env):
    result = filter_env(sample_env, patterns=["DB_*"], filter_name="db-filter")
    assert "db-filter" in str(result)


def test_match_count_and_excluded_count_sum_to_total(sample_env):
    result = filter_env(sample_env, patterns=["DB_*"])
    assert result.match_count + result.excluded_count == len(sample_env)
