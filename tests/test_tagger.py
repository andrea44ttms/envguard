"""Tests for envguard.tagger."""
from __future__ import annotations

import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.tagger import TagIndex, build_tag_index


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add("DATABASE_URL", EnvVarSchema(type=EnvVarType.STRING, required=True, tags=["db", "infra"]))
    s.add("DB_POOL_SIZE", EnvVarSchema(type=EnvVarType.INTEGER, required=False, default="5", tags=["db"]))
    s.add("SECRET_KEY", EnvVarSchema(type=EnvVarType.STRING, required=True, tags=["security"]))
    s.add("DEBUG", EnvVarSchema(type=EnvVarType.BOOLEAN, required=False, default="false", tags=["infra"]))
    s.add("APP_NAME", EnvVarSchema(type=EnvVarType.STRING, required=True))  # no tags
    return s


def test_build_tag_index_all_tags(schema):
    index = build_tag_index(schema)
    assert set(index.all_tags()) == {"db", "infra", "security"}


def test_vars_for_db_tag(schema):
    index = build_tag_index(schema)
    assert index.vars_for_tag("db") == {"DATABASE_URL", "DB_POOL_SIZE"}


def test_vars_for_infra_tag(schema):
    index = build_tag_index(schema)
    assert index.vars_for_tag("infra") == {"DATABASE_URL", "DEBUG"}


def test_vars_for_unknown_tag_returns_empty(schema):
    index = build_tag_index(schema)
    assert index.vars_for_tag("nonexistent") == frozenset()


def test_tags_for_var_multi_tag(schema):
    index = build_tag_index(schema)
    assert index.tags_for_var("DATABASE_URL") == {"db", "infra"}


def test_tags_for_var_single_tag(schema):
    index = build_tag_index(schema)
    assert index.tags_for_var("SECRET_KEY") == {"security"}


def test_tags_for_untagged_var_returns_empty(schema):
    index = build_tag_index(schema)
    assert index.tags_for_var("APP_NAME") == frozenset()


def test_filter_env_by_single_tag(schema):
    index = build_tag_index(schema)
    env = {"DATABASE_URL": "postgres://", "DB_POOL_SIZE": "10", "SECRET_KEY": "abc", "APP_NAME": "myapp"}
    result = index.filter_env(env, ["security"])
    assert result == {"SECRET_KEY": "abc"}


def test_filter_env_by_multiple_tags(schema):
    index = build_tag_index(schema)
    env = {"DATABASE_URL": "postgres://", "DB_POOL_SIZE": "10", "SECRET_KEY": "abc", "DEBUG": "true"}
    result = index.filter_env(env, ["db", "infra"])
    assert set(result.keys()) == {"DATABASE_URL", "DB_POOL_SIZE", "DEBUG"}


def test_filter_env_excludes_untagged_vars(schema):
    index = build_tag_index(schema)
    env = {"APP_NAME": "myapp", "SECRET_KEY": "abc"}
    result = index.filter_env(env, ["db"])
    assert "APP_NAME" not in result


def test_filter_env_unknown_tag_returns_empty(schema):
    index = build_tag_index(schema)
    env = {"DATABASE_URL": "postgres://"}
    result = index.filter_env(env, ["ghost"])
    assert result == {}


def test_all_tags_sorted(schema):
    index = build_tag_index(schema)
    tags = index.all_tags()
    assert tags == sorted(tags)
