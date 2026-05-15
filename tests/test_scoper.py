"""Tests for envguard.scoper."""
import pytest

from envguard.scoper import ScopeResult, scope_env


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "myapp",      # unscoped / global
        "DB_HOST": "prod-db",     # production scope
        "DB_HOST_STG": "stg-db",  # staging scope
        "CACHE_URL": "redis://",  # unscoped / global
        "FEATURE_X": "true",      # staging scope
    }


@pytest.fixture()
def scope_map():
    return {
        "production": ["DB_HOST"],
        "staging": ["DB_HOST_STG", "FEATURE_X"],
    }


def test_returns_scope_result(sample_env, scope_map):
    result = scope_env(sample_env, "production", scope_map)
    assert isinstance(result, ScopeResult)


def test_scope_name_preserved(sample_env, scope_map):
    result = scope_env(sample_env, "production", scope_map)
    assert result.scope == "production"


def test_production_scope_includes_target_key(sample_env, scope_map):
    result = scope_env(sample_env, "production", scope_map)
    assert "DB_HOST" in result.matched


def test_production_scope_excludes_staging_keys(sample_env, scope_map):
    result = scope_env(sample_env, "production", scope_map)
    assert "DB_HOST_STG" not in result.matched
    assert "FEATURE_X" not in result.matched


def test_unscoped_keys_included_by_default(sample_env, scope_map):
    result = scope_env(sample_env, "production", scope_map)
    assert "APP_NAME" in result.matched
    assert "CACHE_URL" in result.matched


def test_exclude_unscoped_omits_globals(sample_env, scope_map):
    result = scope_env(sample_env, "production", scope_map, include_unscoped=False)
    assert "APP_NAME" not in result.matched
    assert "CACHE_URL" not in result.matched
    assert "DB_HOST" in result.matched


def test_excluded_list_contains_other_scope_keys(sample_env, scope_map):
    result = scope_env(sample_env, "production", scope_map)
    assert "DB_HOST_STG" in result.excluded
    assert "FEATURE_X" in result.excluded


def test_match_count_correct(sample_env, scope_map):
    result = scope_env(sample_env, "staging", scope_map)
    # staging keys: DB_HOST_STG, FEATURE_X + unscoped: APP_NAME, CACHE_URL
    assert result.match_count == 4


def test_excluded_count_correct(sample_env, scope_map):
    result = scope_env(sample_env, "staging", scope_map)
    # only DB_HOST is excluded (belongs to production)
    assert result.excluded_count == 1


def test_unknown_scope_returns_only_unscoped(sample_env, scope_map):
    result = scope_env(sample_env, "canary", scope_map)
    assert set(result.matched.keys()) == {"APP_NAME", "CACHE_URL"}


def test_empty_scope_map_includes_all(sample_env):
    result = scope_env(sample_env, "production", {})
    assert result.match_count == len(sample_env)
    assert result.excluded_count == 0


def test_excluded_list_is_sorted(sample_env, scope_map):
    result = scope_env(sample_env, "production", scope_map)
    assert result.excluded == sorted(result.excluded)
