"""Tests for envguard.inspector."""
import pytest
from envguard.inspector import inspect_env, _infer_type, VarInspection
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema("DATABASE_URL", type=EnvVarType.STRING, required=True, tags=["db"]))
    s.add(EnvVarSchema("PORT", type=EnvVarType.INTEGER, required=False, default="8080"))
    s.add(EnvVarSchema("DEBUG", type=EnvVarType.BOOLEAN, required=False, default="false"))
    s.add(EnvVarSchema("API_SECRET", type=EnvVarType.STRING, required=True))
    return s


@pytest.fixture()
def sample_env():
    return {
        "DATABASE_URL": "postgres://localhost/mydb",
        "PORT": "5432",
        "DEBUG": "true",
        "API_SECRET": "supersecret",
        "UNDECLARED_KEY": "somevalue",
    }


# --- _infer_type ---

def test_infer_type_boolean_true():
    assert _infer_type("true") == "boolean"


def test_infer_type_boolean_yes():
    assert _infer_type("yes") == "boolean"


def test_infer_type_integer():
    assert _infer_type("42") == "integer"


def test_infer_type_float():
    assert _infer_type("3.14") == "float"


def test_infer_type_string():
    assert _infer_type("hello") == "string"


def test_infer_type_none_returns_null():
    assert _infer_type(None) == "null"


# --- inspect_env ---

def test_returns_inspection_result(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert len(result) == len(sample_env)


def test_declared_key_marked_as_declared(sample_env, schema):
    result = inspect_env(sample_env, schema)
    insp = result.get("DATABASE_URL")
    assert insp is not None
    assert insp.is_declared is True


def test_undeclared_key_marked_as_not_declared(sample_env, schema):
    result = inspect_env(sample_env, schema)
    insp = result.get("UNDECLARED_KEY")
    assert insp is not None
    assert insp.is_declared is False


def test_required_flag_propagated(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert result.get("DATABASE_URL").is_required is True
    assert result.get("PORT").is_required is False


def test_sensitive_key_flagged(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert result.get("API_SECRET").is_sensitive is True


def test_non_sensitive_key_not_flagged(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert result.get("DATABASE_URL").is_sensitive is False


def test_declared_type_set_for_known_key(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert result.get("PORT").declared_type == EnvVarType.INTEGER.value


def test_declared_type_none_for_undeclared_key(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert result.get("UNDECLARED_KEY").declared_type is None


def test_tags_propagated(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert "db" in result.get("DATABASE_URL").tags


def test_default_value_propagated(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert result.get("PORT").default_value == "8080"


def test_no_schema_still_works():
    env = {"FOO": "bar", "COUNT": "10"}
    result = inspect_env(env)
    assert len(result) == 2
    assert result.get("COUNT").inferred_type == "integer"
    assert result.get("FOO").is_declared is False


def test_get_returns_none_for_missing_key(sample_env, schema):
    result = inspect_env(sample_env, schema)
    assert result.get("NONEXISTENT") is None
