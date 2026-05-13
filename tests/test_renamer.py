"""Tests for envguard.renamer."""
import pytest
from envguard.renamer import rename_env, RenameResult


@pytest.fixture()
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_SECRET": "s3cr3t",
    }


def test_rename_applies_mapping(base_env):
    result = rename_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DATABASE_HOST" in result.renamed
    assert "DB_HOST" not in result.renamed
    assert result.renamed["DATABASE_HOST"] == "localhost"


def test_rename_count_reflects_applied(base_env):
    result = rename_env(base_env, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    assert result.rename_count == 2


def test_original_is_unchanged(base_env):
    rename_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DB_HOST" in base_env  # original dict untouched


def test_missing_key_is_skipped(base_env):
    result = rename_env(base_env, {"MISSING_KEY": "NEW_KEY"})
    assert "MISSING_KEY" in result.skipped
    assert result.rename_count == 0


def test_existing_target_skipped_without_overwrite(base_env):
    env = dict(base_env)
    env["DATABASE_HOST"] = "existing"
    result = rename_env(env, {"DB_HOST": "DATABASE_HOST"}, overwrite=False)
    assert "DB_HOST" in result.skipped
    assert result.renamed["DATABASE_HOST"] == "existing"


def test_existing_target_overwritten_with_flag(base_env):
    env = dict(base_env)
    env["DATABASE_HOST"] = "old_value"
    result = rename_env(env, {"DB_HOST": "DATABASE_HOST"}, overwrite=True)
    assert result.renamed["DATABASE_HOST"] == "localhost"
    assert "DB_HOST" not in result.renamed


def test_unrelated_keys_preserved(base_env):
    result = rename_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    assert result.renamed["DB_PORT"] == "5432"
    assert result.renamed["APP_SECRET"] == "s3cr3t"


def test_empty_mapping_returns_identical_env(base_env):
    result = rename_env(base_env, {})
    assert result.renamed == base_env
    assert result.rename_count == 0


def test_str_output_contains_applied_renames(base_env):
    result = rename_env(base_env, {"DB_HOST": "DATABASE_HOST"})
    text = str(result)
    assert "DB_HOST" in text
    assert "DATABASE_HOST" in text


def test_str_output_contains_skipped_info(base_env):
    result = rename_env(base_env, {"GHOST": "PHANTOM"})
    text = str(result)
    assert "SKIPPED" in text
    assert "GHOST" in text
