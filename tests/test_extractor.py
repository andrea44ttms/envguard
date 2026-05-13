"""Tests for envguard.extractor."""
import pytest

from envguard.extractor import extract_env, ExtractResult
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_ENV": "production",
        "APP_DEBUG": "false",
        "SECRET_KEY": "s3cr3t",
        "LOG_LEVEL": "INFO",
    }


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add("DB_HOST", EnvVarSchema(type=EnvVarType.STRING, required=True, tags=["db"]))
    s.add("DB_PORT", EnvVarSchema(type=EnvVarType.INTEGER, required=True, tags=["db"]))
    s.add("APP_ENV", EnvVarSchema(type=EnvVarType.STRING, required=True, tags=["app"]))
    s.add("APP_DEBUG", EnvVarSchema(type=EnvVarType.BOOLEAN, required=False, tags=["app"]))
    return s


def test_no_selector_no_schema_returns_all(sample_env):
    result = extract_env(sample_env)
    assert result.extract_count == len(sample_env)
    assert result.skip_count == 0


def test_no_selector_with_schema_returns_declared_only(sample_env, schema):
    result = extract_env(sample_env, schema=schema)
    assert set(result.extracted.keys()) == {"DB_HOST", "DB_PORT", "APP_ENV", "APP_DEBUG"}
    assert "SECRET_KEY" in result.skipped
    assert "LOG_LEVEL" in result.skipped


def test_extract_by_explicit_keys(sample_env):
    result = extract_env(sample_env, keys=["DB_HOST", "SECRET_KEY"])
    assert result.extracted == {"DB_HOST": "localhost", "SECRET_KEY": "s3cr3t"}
    assert result.extract_count == 2


def test_extract_by_prefix(sample_env):
    result = extract_env(sample_env, prefixes=["DB_"])
    assert set(result.extracted.keys()) == {"DB_HOST", "DB_PORT"}


def test_extract_by_pattern(sample_env):
    result = extract_env(sample_env, patterns=["APP_*"])
    assert set(result.extracted.keys()) == {"APP_ENV", "APP_DEBUG"}


def test_extract_by_tag(sample_env, schema):
    result = extract_env(sample_env, tags=["db"], schema=schema)
    assert set(result.extracted.keys()) == {"DB_HOST", "DB_PORT"}


def test_selectors_are_or_combined(sample_env):
    result = extract_env(sample_env, keys=["SECRET_KEY"], prefixes=["LOG_"])
    assert set(result.extracted.keys()) == {"SECRET_KEY", "LOG_LEVEL"}


def test_source_count_reflects_input(sample_env):
    result = extract_env(sample_env, keys=["DB_HOST"])
    assert result.source_count == len(sample_env)


def test_str_output_contains_extract_summary(sample_env):
    result = extract_env(sample_env, keys=["DB_HOST"])
    text = str(result)
    assert "Extracted 1" in text
    assert "DB_HOST" in text


def test_missing_explicit_key_is_skipped_silently(sample_env):
    result = extract_env(sample_env, keys=["NONEXISTENT"])
    assert result.extract_count == 0
    assert result.skip_count == len(sample_env)
