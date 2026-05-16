"""Tests for envguard.migrator."""
import pytest
from envguard.migrator import MigrationStep, MigrationResult, migrate_env


@pytest.fixture
def base_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "OLD_SECRET": "hunter2",
        "APP_ENV": "development",
    }


def test_migrate_returns_migration_result(base_env):
    result = migrate_env(base_env, [])
    assert isinstance(result, MigrationResult)


def test_no_steps_returns_identical_env(base_env):
    result = migrate_env(base_env, [])
    assert result.migrated == base_env
    assert result.apply_count == 0
    assert result.skip_count == 0


def test_rename_existing_key(base_env):
    steps = [MigrationStep(action="rename", key="OLD_SECRET", new_key="APP_SECRET")]
    result = migrate_env(base_env, steps)
    assert "APP_SECRET" in result.migrated
    assert "OLD_SECRET" not in result.migrated
    assert result.migrated["APP_SECRET"] == "hunter2"


def test_rename_missing_key_is_skipped(base_env):
    steps = [MigrationStep(action="rename", key="NONEXISTENT", new_key="NEW_KEY")]
    result = migrate_env(base_env, steps)
    assert result.skip_count == 1
    assert result.apply_count == 0
    assert "NEW_KEY" not in result.migrated


def test_patch_overwrites_existing_key(base_env):
    steps = [MigrationStep(action="patch", key="APP_ENV", value="production")]
    result = migrate_env(base_env, steps)
    assert result.migrated["APP_ENV"] == "production"
    assert result.apply_count == 1


def test_patch_adds_new_key(base_env):
    steps = [MigrationStep(action="patch", key="NEW_KEY", value="hello")]
    result = migrate_env(base_env, steps)
    assert result.migrated["NEW_KEY"] == "hello"
    assert result.apply_count == 1


def test_combined_rename_and_patch(base_env):
    steps = [
        MigrationStep(action="rename", key="DB_HOST", new_key="DATABASE_HOST"),
        MigrationStep(action="patch", key="APP_ENV", value="staging"),
    ]
    result = migrate_env(base_env, steps)
    assert "DATABASE_HOST" in result.migrated
    assert "DB_HOST" not in result.migrated
    assert result.migrated["APP_ENV"] == "staging"
    assert result.apply_count == 2
    assert result.skip_count == 0


def test_original_env_is_not_mutated(base_env):
    original_copy = dict(base_env)
    steps = [MigrationStep(action="rename", key="DB_HOST", new_key="DATABASE_HOST")]
    migrate_env(base_env, steps)
    assert base_env == original_copy


def test_unknown_action_is_skipped(base_env):
    steps = [MigrationStep(action="delete", key="DB_HOST")]
    result = migrate_env(base_env, steps)
    assert result.skip_count == 1
    assert result.apply_count == 0


def test_str_representation_contains_counts(base_env):
    steps = [
        MigrationStep(action="rename", key="DB_HOST", new_key="DATABASE_HOST"),
        MigrationStep(action="rename", key="MISSING", new_key="GONE"),
    ]
    result = migrate_env(base_env, steps)
    text = str(result)
    assert "1 applied" in text
    assert "1 skipped" in text
