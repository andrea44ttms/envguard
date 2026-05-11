"""Tests for envguard.grouper module."""
import pytest
from envguard.grouper import group_by_prefix, group_by_categories, EnvGroup, GroupResult
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb",
        "AWS_KEY": "AKIAIOSFODNN7",
        "AWS_SECRET": "wJalrXUtnFEMI",
        "APP_DEBUG": "true",
        "PORT": "8080",
    }


def test_groups_by_prefix(sample_env):
    result = group_by_prefix(sample_env)
    assert "DB" in result.groups
    assert "AWS" in result.groups
    assert "APP" in result.groups


def test_db_group_contains_correct_keys(sample_env):
    result = group_by_prefix(sample_env)
    assert set(result.groups["DB"].keys) == {"DB_HOST", "DB_PORT", "DB_NAME"}


def test_ungrouped_key_has_no_prefix(sample_env):
    result = group_by_prefix(sample_env)
    assert "PORT" in result.ungrouped.keys


def test_total_grouped_count(sample_env):
    result = group_by_prefix(sample_env)
    assert result.total_grouped == 6


def test_group_names_sorted(sample_env):
    result = group_by_prefix(sample_env)
    assert result.group_names == sorted(result.group_names)


def test_schema_filters_undeclared_keys(sample_env):
    schema = EnvSchema()
    schema.add(EnvVarSchema(name="DB_HOST", type=EnvVarType.STRING, required=True))
    schema.add(EnvVarSchema(name="DB_PORT", type=EnvVarType.INTEGER, required=True))
    result = group_by_prefix(sample_env, schema=schema)
    assert set(result.groups["DB"].keys) == {"DB_HOST", "DB_PORT"}
    assert "AWS" not in result.groups


def test_min_prefix_length_excludes_short_prefix():
    env = {"A_THING": "1", "DB_HOST": "localhost"}
    result = group_by_prefix(env, min_prefix_length=2)
    assert "A" not in result.groups
    assert "A_THING" in result.ungrouped.keys
    assert "DB" in result.groups


def test_group_str_output(sample_env):
    result = group_by_prefix(sample_env)
    output = str(result)
    assert "DB" in output
    assert "AWS" in output


def test_group_by_categories(sample_env):
    categories = {
        "database": ["DB_HOST", "DB_PORT", "DB_NAME"],
        "cloud": ["AWS_KEY", "AWS_SECRET"],
    }
    result = group_by_categories(sample_env, categories)
    assert "database" in result.groups
    assert "cloud" in result.groups
    assert set(result.groups["database"].keys) == {"DB_HOST", "DB_PORT", "DB_NAME"}


def test_group_by_categories_ungrouped(sample_env):
    categories = {"database": ["DB_HOST"]}
    result = group_by_categories(sample_env, categories)
    ungrouped_keys = result.ungrouped.keys
    assert "PORT" in ungrouped_keys
    assert "APP_DEBUG" in ungrouped_keys


def test_env_group_len():
    grp = EnvGroup(name="test", keys=["A", "B", "C"])
    assert len(grp) == 3


def test_env_group_str():
    grp = EnvGroup(name="DB", keys=["DB_HOST"], values={"DB_HOST": "localhost"})
    output = str(grp)
    assert "[DB]" in output
    assert "DB_HOST=localhost" in output
