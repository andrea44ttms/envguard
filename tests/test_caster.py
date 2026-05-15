"""Tests for envguard.caster."""
import pytest

from envguard.caster import CastError, CastResult, cast_env
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add("PORT", EnvVarType.INTEGER, required=True)
    s.add("DEBUG", EnvVarType.BOOLEAN, required=False, default="false")
    s.add("RATIO", EnvVarType.FLOAT, required=False)
    s.add("APP_NAME", EnvVarType.STRING, required=True)
    return s


def test_cast_env_returns_cast_result(schema):
    raw = {"PORT": "8080", "APP_NAME": "myapp"}
    result = cast_env(raw, schema)
    assert isinstance(result, CastResult)


def test_integer_cast(schema):
    result = cast_env({"PORT": "3000", "APP_NAME": "x"}, schema)
    assert result.values["PORT"] == 3000
    assert isinstance(result.values["PORT"], int)


def test_boolean_true_variants(schema):
    for val in ("true", "1", "yes", "on"):
        result = cast_env({"PORT": "80", "APP_NAME": "x", "DEBUG": val}, schema)
        assert result.values["DEBUG"] is True, f"expected True for {val!r}"


def test_boolean_false_variants(schema):
    for val in ("false", "0", "no", "off"):
        result = cast_env({"PORT": "80", "APP_NAME": "x", "DEBUG": val}, schema)
        assert result.values["DEBUG"] is False, f"expected False for {val!r}"


def test_float_cast(schema):
    result = cast_env({"PORT": "80", "APP_NAME": "x", "RATIO": "3.14"}, schema)
    assert abs(result.values["RATIO"] - 3.14) < 1e-9


def test_string_cast_unchanged(schema):
    result = cast_env({"PORT": "80", "APP_NAME": "hello world"}, schema)
    assert result.values["APP_NAME"] == "hello world"


def test_invalid_integer_produces_error(schema):
    result = cast_env({"PORT": "not_a_number", "APP_NAME": "x"}, schema)
    assert not result.ok
    assert result.error_count == 1
    err = result.errors[0]
    assert isinstance(err, CastError)
    assert err.key == "PORT"
    assert err.expected_type == "integer"


def test_invalid_boolean_produces_error(schema):
    result = cast_env({"PORT": "80", "APP_NAME": "x", "DEBUG": "maybe"}, schema)
    assert not result.ok
    assert result.errors[0].key == "DEBUG"


def test_undeclared_key_passes_through_as_string(schema):
    result = cast_env({"PORT": "80", "APP_NAME": "x", "EXTRA": "123"}, schema)
    assert result.values["EXTRA"] == "123"  # plain string, no cast
    assert result.ok


def test_ok_true_when_no_errors(schema):
    result = cast_env({"PORT": "8080", "APP_NAME": "app"}, schema)
    assert result.ok


def test_str_representation(schema):
    result = cast_env({"PORT": "bad", "APP_NAME": "x"}, schema)
    text = str(result)
    assert "CastResult" in text
    assert "PORT" in text
