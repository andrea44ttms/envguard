"""Tests for envguard.sanitizer."""
import pytest
from envguard.sanitizer import sanitize_env, SanitizeResult


@pytest.fixture()
def base_env():
    return {
        "APP_NAME": "myapp",
        "DB_URL": "  postgres://localhost/db  ",
        "SECRET": "abc\x00def",
        "MULTILINE": "line1\r\nline2\rline3",
        "CLEAN": "already_clean",
    }


def test_returns_sanitize_result(base_env):
    result = sanitize_env(base_env)
    assert isinstance(result, SanitizeResult)


def test_original_is_unchanged(base_env):
    result = sanitize_env(base_env)
    assert result.original == base_env


def test_strip_whitespace_trims_values(base_env):
    result = sanitize_env(base_env, strip_whitespace=True)
    assert result.sanitized["DB_URL"] == "postgres://localhost/db"


def test_no_strip_whitespace_preserves_spaces(base_env):
    result = sanitize_env(base_env, strip_whitespace=False)
    assert result.sanitized["DB_URL"] == "  postgres://localhost/db  "


def test_removes_null_bytes(base_env):
    result = sanitize_env(base_env, remove_null_bytes=True)
    assert "\x00" not in result.sanitized["SECRET"]
    assert result.sanitized["SECRET"] == "abcdef"


def test_no_remove_null_bytes_preserves_them(base_env):
    result = sanitize_env(base_env, remove_null_bytes=False, strip_whitespace=False)
    assert "\x00" in result.sanitized["SECRET"]


def test_normalize_newlines(base_env):
    result = sanitize_env(base_env, normalize_newlines=True, strip_whitespace=False)
    v = result.sanitized["MULTILINE"]
    assert "\r" not in v
    assert v == "line1\nline2\nline3"


def test_no_normalize_newlines_preserves_cr(base_env):
    result = sanitize_env(base_env, normalize_newlines=False, strip_whitespace=False)
    assert "\r" in result.sanitized["MULTILINE"]


def test_max_value_length_truncates():
    env = {"LONG": "a" * 200}
    result = sanitize_env(env, max_value_length=50)
    assert len(result.sanitized["LONG"]) == 50


def test_max_value_length_none_no_truncation():
    env = {"LONG": "a" * 200}
    result = sanitize_env(env, max_value_length=None)
    assert len(result.sanitized["LONG"]) == 200


def test_change_count_reflects_modified_keys(base_env):
    result = sanitize_env(base_env)
    changed_keys = {c[0] for c in result.changes}
    assert "DB_URL" in changed_keys
    assert "SECRET" in changed_keys
    assert "MULTILINE" in changed_keys
    assert "CLEAN" not in changed_keys
    assert "APP_NAME" not in changed_keys


def test_clean_value_not_in_changes():
    env = {"KEY": "clean_value"}
    result = sanitize_env(env)
    assert result.change_count == 0


def test_str_no_changes():
    env = {"KEY": "value"}
    result = sanitize_env(env)
    assert "no changes" in str(result)


def test_str_with_changes():
    env = {"KEY": "  value  "}
    result = sanitize_env(env)
    assert "1 change" in str(result)
    assert "KEY" in str(result)
