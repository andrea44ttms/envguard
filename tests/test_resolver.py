"""Tests for envguard.resolver."""
from __future__ import annotations

import pytest

from envguard.resolver import ResolveResult, ResolvedVar, resolve_env


@pytest.fixture
def base_source():
    return ("base.env", {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "dev"})


@pytest.fixture
def override_source():
    return ("prod.env", {"DB_HOST": "prod-db", "SECRET_KEY": "s3cr3t"})


def test_empty_sources_returns_empty_result():
    result = resolve_env([])
    assert isinstance(result, ResolveResult)
    assert result.keys == []


def test_single_source_all_keys_resolved(base_source):
    result = resolve_env([base_source])
    assert set(result.keys) == {"DB_HOST", "DB_PORT", "APP_ENV"}


def test_single_source_correct_values(base_source):
    result = resolve_env([base_source])
    assert result.resolved["DB_HOST"].value == "localhost"
    assert result.resolved["DB_PORT"].value == "5432"


def test_single_source_name_recorded(base_source):
    result = resolve_env([base_source])
    assert result.resolved["DB_HOST"].source == "base.env"


def test_higher_priority_source_wins(base_source, override_source):
    result = resolve_env([base_source, override_source])
    assert result.resolved["DB_HOST"].value == "prod-db"
    assert result.resolved["DB_HOST"].source == "prod.env"


def test_lower_priority_key_preserved_when_not_overridden(base_source, override_source):
    result = resolve_env([base_source, override_source])
    assert result.resolved["DB_PORT"].value == "5432"
    assert result.resolved["DB_PORT"].source == "base.env"


def test_new_key_from_override_included(base_source, override_source):
    result = resolve_env([base_source, override_source])
    assert "SECRET_KEY" in result.resolved
    assert result.resolved["SECRET_KEY"].value == "s3cr3t"


def test_to_dict_returns_plain_mapping(base_source, override_source):
    result = resolve_env([base_source, override_source])
    d = result.to_dict()
    assert isinstance(d, dict)
    assert d["DB_HOST"] == "prod-db"
    assert d["APP_ENV"] == "dev"


def test_source_names_recorded(base_source, override_source):
    result = resolve_env([base_source, override_source])
    assert result.source_names == ["base.env", "prod.env"]


def test_str_output_contains_var_count(base_source):
    result = resolve_env([base_source])
    text = str(result)
    assert "3 vars" in text


def test_get_returns_resolved_var(base_source):
    result = resolve_env([base_source])
    var = result.get("DB_HOST")
    assert isinstance(var, ResolvedVar)
    assert var.key == "DB_HOST"


def test_get_missing_key_returns_none(base_source):
    result = resolve_env([base_source])
    assert result.get("MISSING_KEY") is None


def test_three_sources_last_wins():
    s1 = ("s1", {"KEY": "v1"})
    s2 = ("s2", {"KEY": "v2"})
    s3 = ("s3", {"KEY": "v3"})
    result = resolve_env([s1, s2, s3])
    assert result.resolved["KEY"].value == "v3"
    assert result.resolved["KEY"].source == "s3"
