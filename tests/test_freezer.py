"""Tests for envguard.freezer."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envguard.freezer import (
    FrozenEnv,
    diff_frozen,
    freeze_env,
    load_freeze,
    save_freeze,
)


SAMPLE_ENV = {
    "APP_HOST": "localhost",
    "APP_PORT": "8080",
    "DB_PASSWORD": "s3cr3t",
    "API_KEY": "abc123",
}


def test_freeze_env_returns_frozen_env():
    frozen = freeze_env(SAMPLE_ENV)
    assert isinstance(frozen, FrozenEnv)


def test_freeze_env_captures_all_keys():
    frozen = freeze_env(SAMPLE_ENV)
    assert set(frozen.values.keys()) == set(SAMPLE_ENV.keys())


def test_freeze_env_redacts_sensitive_keys():
    frozen = freeze_env(SAMPLE_ENV, redact=True)
    assert frozen.values["DB_PASSWORD"] != "s3cr3t"
    assert frozen.values["API_KEY"] != "abc123"


def test_freeze_env_keeps_sensitive_when_no_redact():
    frozen = freeze_env(SAMPLE_ENV, redact=False)
    assert frozen.values["DB_PASSWORD"] == "s3cr3t"
    assert frozen.values["API_KEY"] == "abc123"


def test_freeze_env_records_redacted_keys():
    frozen = freeze_env(SAMPLE_ENV, redact=True)
    assert "DB_PASSWORD" in frozen.redacted_keys
    assert "API_KEY" in frozen.redacted_keys
    assert "APP_HOST" not in frozen.redacted_keys


def test_freeze_env_captured_at_is_set():
    frozen = freeze_env(SAMPLE_ENV)
    assert frozen.captured_at  # non-empty ISO timestamp


def test_to_dict_contains_expected_keys():
    frozen = freeze_env(SAMPLE_ENV)
    d = frozen.to_dict()
    assert "captured_at" in d
    assert "values" in d
    assert "redacted_keys" in d


def test_save_and_load_roundtrip(tmp_path):
    frozen = freeze_env(SAMPLE_ENV, redact=False)
    dest = tmp_path / "env.freeze.json"
    save_freeze(frozen, dest)
    loaded = load_freeze(dest)
    assert loaded.values == frozen.values
    assert loaded.captured_at == frozen.captured_at


def test_save_creates_valid_json(tmp_path):
    frozen = freeze_env(SAMPLE_ENV)
    dest = tmp_path / "env.freeze.json"
    save_freeze(frozen, dest)
    raw = json.loads(dest.read_text())
    assert isinstance(raw["values"], dict)


def test_diff_frozen_no_changes():
    frozen = freeze_env(SAMPLE_ENV, redact=False)
    changes = diff_frozen(frozen, dict(SAMPLE_ENV), redact=False)
    assert changes == {}


def test_diff_frozen_detects_changed_value():
    frozen = freeze_env(SAMPLE_ENV, redact=False)
    current = {**SAMPLE_ENV, "APP_PORT": "9090"}
    changes = diff_frozen(frozen, current, redact=False)
    assert "APP_PORT" in changes
    assert changes["APP_PORT"]["before"] == "8080"
    assert changes["APP_PORT"]["after"] == "9090"


def test_diff_frozen_detects_added_key():
    frozen = freeze_env(SAMPLE_ENV, redact=False)
    current = {**SAMPLE_ENV, "NEW_VAR": "hello"}
    changes = diff_frozen(frozen, current, redact=False)
    assert "NEW_VAR" in changes
    assert changes["NEW_VAR"]["before"] is None


def test_diff_frozen_detects_removed_key():
    frozen = freeze_env(SAMPLE_ENV, redact=False)
    current = {k: v for k, v in SAMPLE_ENV.items() if k != "APP_HOST"}
    changes = diff_frozen(frozen, current, redact=False)
    assert "APP_HOST" in changes
    assert changes["APP_HOST"]["after"] is None


def test_diff_frozen_redacts_sensitive_in_after():
    frozen = freeze_env(SAMPLE_ENV, redact=False)
    current = {**SAMPLE_ENV, "DB_PASSWORD": "newpassword"}
    changes = diff_frozen(frozen, current, redact=True)
    assert changes["DB_PASSWORD"]["after"] != "newpassword"
