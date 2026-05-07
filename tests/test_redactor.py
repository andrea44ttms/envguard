"""Tests for envguard.redactor."""

import pytest

from envguard.redactor import (
    _REDACTED_PLACEHOLDER,
    is_sensitive,
    redact_dict,
    redact_env,
    redact_value,
)


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------


def test_is_sensitive_detects_password():
    assert is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_detects_token():
    assert is_sensitive("GITHUB_TOKEN") is True


def test_is_sensitive_detects_api_key():
    assert is_sensitive("STRIPE_API_KEY") is True


def test_is_sensitive_case_insensitive():
    assert is_sensitive("db_secret") is True


def test_is_sensitive_returns_false_for_plain_key():
    assert is_sensitive("APP_PORT") is False


def test_is_sensitive_extra_keywords():
    assert is_sensitive("INTERNAL_CERT", extra_keywords=["cert"]) is True


def test_is_sensitive_extra_keywords_no_false_positive():
    assert is_sensitive("APP_PORT", extra_keywords=["cert"]) is False


# ---------------------------------------------------------------------------
# redact_value
# ---------------------------------------------------------------------------


def test_redact_value_masks_sensitive():
    result = redact_value("DB_PASSWORD", "supersecret")
    assert result == _REDACTED_PLACEHOLDER


def test_redact_value_passes_through_plain():
    result = redact_value("APP_PORT", "8080")
    assert result == "8080"


def test_redact_value_custom_placeholder():
    result = redact_value("API_KEY", "abc123", placeholder="<hidden>")
    assert result == "<hidden>"


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------


def test_redact_env_masks_sensitive_keys():
    env = {"APP_NAME": "myapp", "DB_PASSWORD": "s3cr3t", "AUTH_TOKEN": "tok"}
    redacted = redact_env(env)
    assert redacted["APP_NAME"] == "myapp"
    assert redacted["DB_PASSWORD"] == _REDACTED_PLACEHOLDER
    assert redacted["AUTH_TOKEN"] == _REDACTED_PLACEHOLDER


def test_redact_env_returns_new_dict():
    env = {"APP_NAME": "myapp"}
    redacted = redact_env(env)
    assert redacted is not env


def test_redact_env_empty_input():
    assert redact_env({}) == {}


# ---------------------------------------------------------------------------
# redact_dict
# ---------------------------------------------------------------------------


def test_redact_dict_masks_explicit_keys():
    data = {"HOST": "localhost", "PORT": "5432", "PASS": "hunter2"}
    redacted = redact_dict(data, sensitive_keys=["PASS"])
    assert redacted["HOST"] == "localhost"
    assert redacted["PORT"] == "5432"
    assert redacted["PASS"] == _REDACTED_PLACEHOLDER


def test_redact_dict_case_insensitive_keys():
    data = {"MySecret": "value"}
    redacted = redact_dict(data, sensitive_keys=["mysecret"])
    assert redacted["MySecret"] == _REDACTED_PLACEHOLDER


def test_redact_dict_no_sensitive_keys():
    data = {"HOST": "localhost"}
    redacted = redact_dict(data, sensitive_keys=[])
    assert redacted == data
