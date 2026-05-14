"""Tests for envguard.classifier."""
import pytest
from envguard.classifier import classify_env, ClassificationResult, _classify_key


@pytest.fixture()
def sample_env():
    return {
        "DATABASE_URL": "postgres://localhost/mydb",
        "DB_HOST": "localhost",
        "REDIS_URL": "redis://localhost:6379",
        "SECRET_KEY": "supersecret",
        "API_KEY": "abc123",
        "LOG_LEVEL": "INFO",
        "PORT": "8080",
        "APP_ENV": "production",
        "FOOBAR": "baz",
    }


def test_classify_env_returns_classification_result(sample_env):
    result = classify_env(sample_env)
    assert isinstance(result, ClassificationResult)


def test_database_keys_classified_correctly(sample_env):
    result = classify_env(sample_env)
    assert "DATABASE_URL" in result.vars_for("database")
    assert "DB_HOST" in result.vars_for("database")


def test_cache_key_classified(sample_env):
    result = classify_env(sample_env)
    assert "REDIS_URL" in result.vars_for("cache")


def test_security_keys_classified(sample_env):
    result = classify_env(sample_env)
    security = result.vars_for("security")
    assert "SECRET_KEY" in security
    assert "API_KEY" in security


def test_observability_key_classified(sample_env):
    result = classify_env(sample_env)
    assert "LOG_LEVEL" in result.vars_for("observability")


def test_networking_key_classified(sample_env):
    result = classify_env(sample_env)
    assert "PORT" in result.vars_for("networking")


def test_runtime_key_classified(sample_env):
    result = classify_env(sample_env)
    assert "APP_ENV" in result.vars_for("runtime")


def test_uncategorized_key(sample_env):
    result = classify_env(sample_env)
    assert "FOOBAR" in result.vars_for("uncategorized")


def test_category_of_returns_correct_category(sample_env):
    result = classify_env(sample_env)
    assert result.category_of("DATABASE_URL") == "database"
    assert result.category_of("FOOBAR") == "uncategorized"


def test_category_names_are_sorted(sample_env):
    result = classify_env(sample_env)
    assert result.category_names == sorted(result.category_names)


def test_vars_for_unknown_category_returns_empty(sample_env):
    result = classify_env(sample_env)
    assert result.vars_for("nonexistent") == []


def test_str_representation(sample_env):
    result = classify_env(sample_env)
    text = str(result)
    assert "ClassificationResult" in text
    assert "database" in text


def test_empty_env_gives_empty_result():
    result = classify_env({})
    assert result.categories == {}
    assert result.category_names == []


def test_classify_key_direct():
    assert _classify_key("MY_SECRET_VALUE") == "security"
    assert _classify_key("RANDOM_STUFF") == "uncategorized"
