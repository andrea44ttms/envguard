"""Tests for envguard.interpolator."""

import pytest

from envguard.interpolator import InterpolationError, interpolate


def test_no_placeholders_returned_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    assert interpolate(env) == env


def test_braced_placeholder_resolved_from_env():
    env = {"BASE": "/app", "LOG_DIR": "${BASE}/logs"}
    result = interpolate(env)
    assert result["LOG_DIR"] == "/app/logs"


def test_unbraced_placeholder_resolved_from_env():
    env = {"USER": "alice", "GREETING": "Hello $USER"}
    result = interpolate(env)
    assert result["GREETING"] == "Hello alice"


def test_placeholder_resolved_from_context():
    env = {"DSN": "postgres://${DB_HOST}:5432/mydb"}
    context = {"DB_HOST": "db.example.com"}
    result = interpolate(env, context=context)
    assert result["DSN"] == "postgres://db.example.com:5432/mydb"


def test_env_takes_precedence_over_context():
    env = {"VAR": "from_env", "MSG": "value=${VAR}"}
    context = {"VAR": "from_context"}
    result = interpolate(env, context=context)
    assert result["MSG"] == "value=from_env"


def test_multiple_placeholders_in_one_value():
    env = {"A": "foo", "B": "bar", "C": "${A}-${B}"}
    result = interpolate(env)
    assert result["C"] == "foo-bar"


def test_strict_mode_raises_on_missing_var():
    env = {"URL": "http://${UNDEFINED_HOST}/path"}
    with pytest.raises(InterpolationError) as exc_info:
        interpolate(env, strict=True)
    assert "UNDEFINED_HOST" in str(exc_info.value)
    assert "URL" in str(exc_info.value)


def test_non_strict_mode_leaves_placeholder_intact():
    env = {"URL": "http://${MISSING}/path"}
    result = interpolate(env, strict=False)
    assert result["URL"] == "http://${MISSING}/path"


def test_interpolation_error_attributes():
    env = {"KEY": "${NO_SUCH_VAR}"}
    with pytest.raises(InterpolationError) as exc_info:
        interpolate(env)
    err = exc_info.value
    assert err.var == "NO_SUCH_VAR"
    assert err.referencing_key == "KEY"


def test_original_env_not_mutated():
    env = {"A": "hello", "B": "${A} world"}
    original = dict(env)
    interpolate(env)
    assert env == original
