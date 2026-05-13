"""Tests for envguard.patcher."""
from __future__ import annotations

import pytest

from envguard.patcher import patch_env, write_patch


@pytest.fixture()
def base_env() -> dict[str, str]:
    return {
        "APP_HOST": "localhost",
        "APP_PORT": "8000",
        "DB_PASSWORD": "secret",
        "DEBUG": "true",
    }


def test_no_changes_when_updates_empty(base_env):
    result = patch_env(base_env, {})
    assert result.change_count == 0
    assert result.updated == {}
    assert result.added == {}
    assert result.removed == []


def test_update_existing_key(base_env):
    result = patch_env(base_env, {"APP_PORT": "9000"})
    assert "APP_PORT" in result.updated
    assert result.updated["APP_PORT"] == "9000"
    assert result.change_count == 1


def test_update_with_same_value_not_counted(base_env):
    result = patch_env(base_env, {"APP_HOST": "localhost"})
    assert "APP_HOST" not in result.updated
    assert result.change_count == 0


def test_add_new_key(base_env):
    result = patch_env(base_env, {"NEW_KEY": "new_value"})
    assert "NEW_KEY" in result.added
    assert result.change_count == 1


def test_remove_key(base_env):
    result = patch_env(base_env, {}, remove_keys=["DEBUG"])
    assert "DEBUG" in result.removed
    assert result.change_count == 1
    assert all("DEBUG" not in line for line in result.patched_lines)


def test_remove_key_not_in_source_is_ignored(base_env):
    result = patch_env(base_env, {}, remove_keys=["NONEXISTENT"])
    assert result.removed == []
    assert result.change_count == 0


def test_combined_operations(base_env):
    result = patch_env(
        base_env,
        {"APP_PORT": "9000", "LOG_LEVEL": "info"},
        remove_keys=["DEBUG"],
    )
    assert result.change_count == 3
    assert "APP_PORT" in result.updated
    assert "LOG_LEVEL" in result.added
    assert "DEBUG" in result.removed


def test_patched_lines_contain_updated_value(base_env):
    result = patch_env(base_env, {"APP_PORT": "9999"})
    assert "APP_PORT=9999" in result.patched_lines


def test_original_lines_preserved(base_env):
    result = patch_env(base_env, {"APP_PORT": "9999"})
    assert "APP_PORT=8000" in result.original_lines


def test_write_patch_creates_file(tmp_path, base_env):
    result = patch_env(base_env, {"APP_PORT": "9000"})
    out = tmp_path / ".env"
    write_patch(out, result)
    content = out.read_text()
    assert "APP_PORT=9000" in content
    assert content.endswith("\n")
