"""Tests for envguard.aliaser."""
import pytest

from envguard.aliaser import AliasMapping, AliasResult, resolve_aliases


@pytest.fixture()
def base_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DATABASE_URL": "postgres://localhost/mydb",
        "SECRET_KEY": "s3cr3t",
    }


@pytest.fixture()
def mappings() -> list:
    return [
        AliasMapping(alias="DB_HOST", canonical="DATABASE_HOST", description="legacy"),
        AliasMapping(alias="SECRET_KEY", canonical="APP_SECRET"),
    ]


def test_resolve_aliases_returns_alias_result(base_env, mappings):
    result = resolve_aliases(base_env, mappings)
    assert isinstance(result, AliasResult)


def test_alias_key_renamed_to_canonical(base_env, mappings):
    result = resolve_aliases(base_env, mappings)
    assert "DATABASE_HOST" in result.resolved
    assert "DB_HOST" not in result.resolved


def test_alias_value_preserved(base_env, mappings):
    result = resolve_aliases(base_env, mappings)
    assert result.resolved["DATABASE_HOST"] == "localhost"


def test_apply_count_reflects_applied(base_env, mappings):
    result = resolve_aliases(base_env, mappings)
    assert result.apply_count == 2


def test_original_env_not_mutated(base_env, mappings):
    original_keys = set(base_env.keys())
    resolve_aliases(base_env, mappings)
    assert set(base_env.keys()) == original_keys


def test_canonical_already_present_is_skipped(mappings):
    env = {"DB_HOST": "localhost", "DATABASE_HOST": "remotehost"}
    result = resolve_aliases(env, [mappings[0]])
    assert result.apply_count == 0
    assert "DB_HOST" in result.skipped
    assert result.resolved["DATABASE_HOST"] == "remotehost"


def test_overwrite_replaces_canonical(mappings):
    env = {"DB_HOST": "localhost", "DATABASE_HOST": "remotehost"}
    result = resolve_aliases(env, [mappings[0]], overwrite=True)
    assert result.apply_count == 1
    assert result.resolved["DATABASE_HOST"] == "localhost"


def test_missing_alias_key_ignored(base_env):
    mappings = [AliasMapping(alias="NONEXISTENT", canonical="TARGET")]
    result = resolve_aliases(base_env, mappings)
    assert result.apply_count == 0
    assert "TARGET" not in result.resolved


def test_unrelated_keys_preserved(base_env, mappings):
    result = resolve_aliases(base_env, mappings)
    assert "DATABASE_URL" in result.resolved
    assert result.resolved["DATABASE_URL"] == "postgres://localhost/mydb"


def test_str_output_includes_applied_and_skipped():
    env = {"OLD_KEY": "val", "NEW_KEY": "existing"}
    mappings = [
        AliasMapping(alias="OLD_KEY", canonical="NEW_KEY"),
    ]
    result = resolve_aliases(env, mappings)
    text = str(result)
    assert "skipped" in text
    assert "OLD_KEY" in text


def test_alias_mapping_str_includes_description():
    m = AliasMapping(alias="LEGACY", canonical="CURRENT", description="v1 compat")
    assert "v1 compat" in str(m)
    assert "LEGACY" in str(m)
    assert "CURRENT" in str(m)
