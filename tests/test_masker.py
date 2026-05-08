"""Tests for envguard.masker."""

import pytest
from envguard.masker import mask_env, _full_mask, _partial_mask, _DEFAULT_MASK


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "supersecret",
        "API_KEY": "abc123xyz789",
        "PORT": "8080",
        "SECRET_TOKEN": "tok_live_abcdefgh1234",
    }


def test_non_sensitive_values_unchanged(sample_env):
    result = mask_env(sample_env)
    assert result.masked["APP_NAME"] == "myapp"
    assert result.masked["PORT"] == "8080"


def test_sensitive_values_fully_masked(sample_env):
    result = mask_env(sample_env)
    assert result.masked["DB_PASSWORD"] == _DEFAULT_MASK
    assert result.masked["API_KEY"] == _DEFAULT_MASK
    assert result.masked["SECRET_TOKEN"] == _DEFAULT_MASK


def test_partial_mask_reveals_edges(sample_env):
    result = mask_env(sample_env, partial=True)
    masked_pw = result.masked["DB_PASSWORD"]
    assert masked_pw.startswith("supe")
    assert masked_pw.endswith("cret")
    assert _DEFAULT_MASK in masked_pw


def test_partial_mask_short_value_fully_masked():
    env = {"DB_PASSWORD": "short"}
    result = mask_env(env, partial=True)
    assert result.masked["DB_PASSWORD"] == _DEFAULT_MASK


def test_extra_keys_are_masked(sample_env):
    result = mask_env(sample_env, extra_keys=["APP_NAME"])
    assert result.masked["APP_NAME"] == _DEFAULT_MASK


def test_extra_keys_case_insensitive(sample_env):
    result = mask_env(sample_env, extra_keys=["app_name"])
    assert result.masked["APP_NAME"] == _DEFAULT_MASK


def test_custom_mask_string(sample_env):
    result = mask_env(sample_env, mask="[HIDDEN]")
    assert result.masked["DB_PASSWORD"] == "[HIDDEN]"


def test_masked_count_reflects_sensitive_keys(sample_env):
    result = mask_env(sample_env)
    # DB_PASSWORD, API_KEY, SECRET_TOKEN => 3
    assert result.masked_count == 3


def test_masked_count_includes_extra_keys(sample_env):
    result = mask_env(sample_env, extra_keys=["PORT"])
    assert result.masked_count == 4


def test_str_output_contains_all_keys(sample_env):
    result = mask_env(sample_env)
    output = str(result)
    for key in sample_env:
        assert key in output


def test_original_dict_is_unchanged(sample_env):
    original_copy = dict(sample_env)
    mask_env(sample_env)
    assert sample_env == original_copy


def test_empty_env_returns_empty_result():
    result = mask_env({})
    assert result.masked == {}
    assert result.masked_count == 0
