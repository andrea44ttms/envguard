"""Tests for the core schema validation feature."""

import pytest

from envguard import EnvSchema, EnvVarSchema, EnvVarType, EnvValidator


@pytest.fixture
def base_schema() -> EnvSchema:
    schema = EnvSchema()
    schema.add(EnvVarSchema(name="APP_NAME", required=True))
    schema.add(EnvVarSchema(name="PORT", var_type=EnvVarType.INTEGER, required=True))
    schema.add(EnvVarSchema(name="DEBUG", var_type=EnvVarType.BOOLEAN, default="false"))
    schema.add(EnvVarSchema(name="API_URL", var_type=EnvVarType.URL, required=True))
    schema.add(EnvVarSchema(
        name="ENV",
        allowed_values=["development", "staging", "production"],
        default="development",
    ))
    return schema


def test_valid_env_passes(base_schema):
    env = {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "DEBUG": "true",
        "API_URL": "https://api.example.com",
        "ENV": "production",
    }
    result = EnvValidator(base_schema).validate(env)
    assert result.is_valid
    assert result.error_count == 0


def test_missing_required_var(base_schema):
    env = {"PORT": "8080", "API_URL": "https://api.example.com"}
    result = EnvValidator(base_schema).validate(env)
    assert not result.is_valid
    variables_with_errors = {e.variable for e in result.errors}
    assert "APP_NAME" in variables_with_errors


def test_invalid_integer_type(base_schema):
    env = {
        "APP_NAME": "myapp",
        "PORT": "not-a-number",
        "API_URL": "https://api.example.com",
    }
    result = EnvValidator(base_schema).validate(env)
    assert not result.is_valid
    assert any(e.variable == "PORT" for e in result.errors)


def test_invalid_boolean(base_schema):
    env = {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "DEBUG": "yes",
        "API_URL": "https://api.example.com",
    }
    result = EnvValidator(base_schema).validate(env)
    assert not result.is_valid
    assert any(e.variable == "DEBUG" for e in result.errors)


def test_invalid_url(base_schema):
    env = {"APP_NAME": "myapp", "PORT": "8080", "API_URL": "not-a-url"}
    result = EnvValidator(base_schema).validate(env)
    assert not result.is_valid
    assert any(e.variable == "API_URL" for e in result.errors)


def test_disallowed_value(base_schema):
    env = {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "API_URL": "https://api.example.com",
        "ENV": "local",
    }
    result = EnvValidator(base_schema).validate(env)
    assert not result.is_valid
    assert any(e.variable == "ENV" for e in result.errors)


def test_min_max_length():
    schema = EnvSchema()
    schema.add(EnvVarSchema(name="SECRET", min_length=8, max_length=32))
    validator = EnvValidator(schema)

    assert not validator.validate({"SECRET": "short"}).is_valid
    assert not validator.validate({"SECRET": "x" * 33}).is_valid
    assert validator.validate({"SECRET": "validpassword"}).is_valid


def test_raise_if_invalid(base_schema):
    env = {}  # all required vars missing
    result = EnvValidator(base_schema).validate(env)
    with pytest.raises(ValueError, match="validation error"):
        result.raise_if_invalid()


def test_summary_valid(base_schema):
    env = {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "API_URL": "https://api.example.com",
    }
    result = EnvValidator(base_schema).validate(env)
    assert "valid" in result.summary().lower()
