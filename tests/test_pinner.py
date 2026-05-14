"""Tests for envguard.pinner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envguard.pinner import (
    PinEntry,
    PinResult,
    diff_pin,
    load_pin,
    pin_env,
    save_pin,
)


SAMPLE_ENV = {
    "APP_NAME": "myapp",
    "DB_PASSWORD": "s3cr3t",
    "PORT": "8080",
    "API_KEY": "abc123",
}


def test_pin_env_returns_pin_result():
    result = pin_env(SAMPLE_ENV)
    assert isinstance(result, PinResult)


def test_pin_env_count_matches_input():
    result = pin_env(SAMPLE_ENV)
    assert result.count == len(SAMPLE_ENV)


def test_pin_env_redacts_sensitive_keys_by_default():
    result = pin_env(SAMPLE_ENV)
    sensitive = {e.key: e for e in result.entries if e.redacted}
    assert "DB_PASSWORD" in sensitive
    assert "API_KEY" in sensitive
    assert sensitive["DB_PASSWORD"].value != "s3cr3t"


def test_pin_env_keeps_plain_values_unchanged():
    result = pin_env(SAMPLE_ENV)
    plain = {e.key: e for e in result.entries if not e.redacted}
    assert plain["APP_NAME"].value == "myapp"
    assert plain["PORT"].value == "8080"


def test_pin_env_no_redact_flag_preserves_all():
    result = pin_env(SAMPLE_ENV, redact=False)
    assert all(not e.redacted for e in result.entries)
    values = {e.key: e.value for e in result.entries}
    assert values["DB_PASSWORD"] == "s3cr3t"


def test_pin_env_entries_are_sorted():
    result = pin_env(SAMPLE_ENV)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_pin_env_source_stored():
    result = pin_env(SAMPLE_ENV, source=".env.staging")
    assert result.source == ".env.staging"


def test_pin_result_to_dict_structure():
    result = pin_env({"FOO": "bar"}, redact=False)
    d = result.to_dict()
    assert "pinned_at" in d
    assert "entries" in d
    assert d["entries"][0]["key"] == "FOO"


def test_save_and_load_pin_roundtrip(tmp_path):
    lock = str(tmp_path / "env.lock")
    result = pin_env(SAMPLE_ENV)
    save_pin(result, lock)
    loaded = load_pin(lock)
    assert loaded is not None
    assert loaded.count == result.count
    assert loaded.pinned_at == result.pinned_at


def test_load_pin_returns_none_when_missing(tmp_path):
    assert load_pin(str(tmp_path / "nonexistent.lock")) is None


def test_diff_pin_detects_changed_value():
    prev = pin_env({"FOO": "old"}, redact=False)
    curr = pin_env({"FOO": "new"}, redact=False)
    changes = diff_pin(curr, prev)
    assert "FOO" in changes
    assert changes["FOO"] == {"old": "old", "new": "new"}


def test_diff_pin_detects_added_key():
    prev = pin_env({"A": "1"}, redact=False)
    curr = pin_env({"A": "1", "B": "2"}, redact=False)
    changes = diff_pin(curr, prev)
    assert "B" in changes
    assert changes["B"]["old"] is None


def test_diff_pin_detects_removed_key():
    prev = pin_env({"A": "1", "B": "2"}, redact=False)
    curr = pin_env({"A": "1"}, redact=False)
    changes = diff_pin(curr, prev)
    assert "B" in changes
    assert changes["B"]["new"] is None


def test_diff_pin_no_changes_when_identical():
    result = pin_env(SAMPLE_ENV)
    assert diff_pin(result, result) == {}


def test_str_output_contains_keys():
    result = pin_env({"FOO": "bar"}, redact=False)
    text = str(result)
    assert "FOO=bar" in text
