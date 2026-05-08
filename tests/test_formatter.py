"""Tests for envguard.formatter."""

import pytest
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.formatter import format_env, FormattedEnv


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add("PORT", EnvVarSchema(type=EnvVarType.INTEGER, required=True))
    s.add("DEBUG", EnvVarSchema(type=EnvVarType.BOOLEAN, required=False, default="false"))
    s.add("RATE", EnvVarSchema(type=EnvVarType.FLOAT, required=False))
    s.add("APP_NAME", EnvVarSchema(type=EnvVarType.STRING, required=True))
    return s


def test_integer_cast(schema):
    result = format_env({"PORT": "8080", "APP_NAME": "myapp"}, schema)
    assert result.get("PORT") == 8080
    assert isinstance(result.get("PORT"), int)


def test_boolean_true_variants(schema):
    for val in ("true", "1", "yes"):
        result = format_env({"PORT": "80", "APP_NAME": "x", "DEBUG": val}, schema)
        assert result.get("DEBUG") is True


def test_boolean_false_variant(schema):
    result = format_env({"PORT": "80", "APP_NAME": "x", "DEBUG": "false"}, schema)
    assert result.get("DEBUG") is False


def test_float_cast(schema):
    result = format_env({"PORT": "80", "APP_NAME": "x", "RATE": "3.14"}, schema)
    assert result.get("RATE") == pytest.approx(3.14)


def test_string_kept_as_str(schema):
    result = format_env({"PORT": "80", "APP_NAME": "envguard"}, schema)
    assert result.get("APP_NAME") == "envguard"
    assert isinstance(result.get("APP_NAME"), str)


def test_default_applied_when_key_absent(schema):
    result = format_env({"PORT": "80", "APP_NAME": "x"}, schema)
    # DEBUG has default "false" -> should be cast to bool False
    assert result.get("DEBUG") is False


def test_missing_required_without_default_excluded(schema):
    result = format_env({"APP_NAME": "x"}, schema)
    assert result.get("PORT") is None


def test_invalid_integer_skipped_not_raised(schema):
    result = format_env({"PORT": "not_a_number", "APP_NAME": "x"}, schema)
    assert result.get("PORT") is None


def test_to_dict_returns_copy(schema):
    result = format_env({"PORT": "9000", "APP_NAME": "app"}, schema)
    d = result.to_dict()
    assert isinstance(d, dict)
    assert d["PORT"] == 9000


def test_require_raises_for_missing_key(schema):
    result = format_env({"APP_NAME": "x"}, schema)
    with pytest.raises(KeyError, match="PORT"):
        result.require("PORT")


def test_require_returns_value_when_present(schema):
    result = format_env({"PORT": "443", "APP_NAME": "x"}, schema)
    assert result.require("PORT") == 443


def test_repr_contains_keys(schema):
    result = format_env({"PORT": "80", "APP_NAME": "x"}, schema)
    r = repr(result)
    assert "FormattedEnv" in r
    assert "PORT" in r
