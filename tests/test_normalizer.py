"""Tests for envguard.normalizer."""

import pytest
from envguard.normalizer import NormalizeOptions, normalize_env


def test_uppercase_keys_by_default():
    result = normalize_env({"db_host": "localhost", "Port": "5432"})
    assert "DB_HOST" in result.env
    assert "PORT" in result.env


def test_renamed_keys_tracked():
    result = normalize_env({"db_host": "localhost"})
    assert "db_host" in result.renamed_keys
    assert result.renamed_keys["db_host"] == "DB_HOST"


def test_no_rename_when_already_uppercase():
    result = normalize_env({"DB_HOST": "localhost"})
    assert result.renamed_keys == {}


def test_strip_values_by_default():
    result = normalize_env({"KEY": "  value  "})
    assert result.env["KEY"] == "value"


def test_strip_keys_by_default():
    result = normalize_env({"  KEY  ": "val"})
    assert "KEY" in result.env


def test_drop_empty_values_when_enabled():
    opts = NormalizeOptions(drop_empty_values=True)
    result = normalize_env({"PRESENT": "hello", "EMPTY": ""}, options=opts)
    assert "PRESENT" in result.env
    assert "EMPTY" not in result.env
    assert "EMPTY" in result.dropped_keys


def test_empty_values_kept_by_default():
    result = normalize_env({"EMPTY": ""})
    assert "EMPTY" in result.env
    assert result.env["EMPTY"] == ""


def test_key_prefix_filter():
    opts = NormalizeOptions(key_prefix="APP_")
    raw = {"APP_HOST": "localhost", "DB_PORT": "5432", "APP_DEBUG": "true"}
    result = normalize_env(raw, options=opts)
    assert set(result.env.keys()) == {"APP_HOST", "APP_DEBUG"}
    assert "DB_PORT" in result.dropped_keys


def test_key_prefix_filter_respects_uppercase_option():
    opts = NormalizeOptions(uppercase_keys=True, key_prefix="APP_")
    raw = {"app_host": "localhost", "db_port": "5432"}
    result = normalize_env(raw, options=opts)
    assert "APP_HOST" in result.env
    assert "DB_PORT" not in result.env


def test_change_count_reflects_renames_and_drops():
    opts = NormalizeOptions(drop_empty_values=True)
    raw = {"lower": "val", "EMPTY": ""}
    result = normalize_env(raw, options=opts)
    # 'lower' renamed to 'LOWER', 'EMPTY' dropped
    assert result.change_count == 2


def test_no_changes_on_clean_input():
    result = normalize_env({"DB_HOST": "localhost", "PORT": "5432"})
    assert result.change_count == 0


def test_uppercase_disabled():
    opts = NormalizeOptions(uppercase_keys=False)
    result = normalize_env({"db_host": "localhost"}, options=opts)
    assert "db_host" in result.env
    assert result.renamed_keys == {}
