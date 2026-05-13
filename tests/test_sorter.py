"""Tests for envguard.sorter."""
from __future__ import annotations

import pytest

from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.sorter import SortOrder, SortResult, sort_env


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema("ZEBRA", type=EnvVarType.STRING, required=True))
    s.add(EnvVarSchema("ALPHA", type=EnvVarType.INTEGER, required=True))
    s.add(EnvVarSchema("MANGO", type=EnvVarType.BOOLEAN, required=False, default="false"))
    s.add(EnvVarSchema("BETA", type=EnvVarType.FLOAT, required=False, default="1.0"))
    return s


@pytest.fixture()
def env() -> dict:
    return {"ZEBRA": "z", "ALPHA": "1", "MANGO": "true", "BETA": "3.14", "EXTRA": "x"}


# ---------------------------------------------------------------------------
# alpha sort
# ---------------------------------------------------------------------------

def test_alpha_sort_returns_sort_result(schema, env):
    result = sort_env(env, schema, order=SortOrder.ALPHA)
    assert isinstance(result, SortResult)
    assert result.order == SortOrder.ALPHA


def test_alpha_sort_keys_are_sorted(schema, env):
    result = sort_env(env, schema, order=SortOrder.ALPHA)
    keys = list(result.sorted_env.keys())
    assert keys == sorted(keys)


def test_alpha_sort_preserves_values(schema, env):
    result = sort_env(env, schema, order=SortOrder.ALPHA)
    for k, v in env.items():
        assert result.sorted_env[k] == v


# ---------------------------------------------------------------------------
# type sort
# ---------------------------------------------------------------------------

def test_type_sort_groups_by_type(schema, env):
    result = sort_env(env, schema, order=SortOrder.TYPE)
    assert result.sections  # sections populated
    # boolean, float, integer, string buckets expected
    assert "boolean" in result.sections or "string" in result.sections


def test_type_sort_unknown_key_in_unknown_bucket(schema, env):
    result = sort_env(env, schema, order=SortOrder.TYPE)
    assert "unknown" in result.sections
    assert "EXTRA" in result.sections["unknown"]


# ---------------------------------------------------------------------------
# required-first sort
# ---------------------------------------------------------------------------

def test_required_first_required_keys_come_before_optional(schema, env):
    result = sort_env(env, schema, order=SortOrder.REQUIRED_FIRST)
    keys = list(result.sorted_env.keys())
    required_indices = [keys.index(k) for k in result.sections.get("required", [])]
    optional_indices = [keys.index(k) for k in result.sections.get("optional", [])]
    if required_indices and optional_indices:
        assert max(required_indices) < min(optional_indices)


def test_required_first_sections_populated(schema, env):
    result = sort_env(env, schema, order=SortOrder.REQUIRED_FIRST)
    assert "required" in result.sections
    assert set(result.sections["required"]) == {"ZEBRA", "ALPHA"}


def test_required_first_unknown_key_in_unknown_section(schema, env):
    result = sort_env(env, schema, order=SortOrder.REQUIRED_FIRST)
    assert "EXTRA" in result.sections.get("unknown", [])


# ---------------------------------------------------------------------------
# declaration sort
# ---------------------------------------------------------------------------

def test_declaration_sort_follows_schema_order(schema, env):
    result = sort_env(env, schema, order=SortOrder.DECLARATION)
    keys = list(result.sorted_env.keys())
    # schema order: ZEBRA, ALPHA, MANGO, BETA — EXTRA appended after
    assert keys.index("ZEBRA") < keys.index("ALPHA")
    assert keys.index("ALPHA") < keys.index("MANGO")
    assert keys.index("MANGO") < keys.index("BETA")


def test_declaration_sort_undeclared_key_appended(schema, env):
    result = sort_env(env, schema, order=SortOrder.DECLARATION)
    keys = list(result.sorted_env.keys())
    assert "EXTRA" in keys
    assert keys.index("EXTRA") > keys.index("BETA")


# ---------------------------------------------------------------------------
# original_env preserved across all orders
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("order", list(SortOrder))
def test_original_env_unchanged(schema, env, order):
    result = sort_env(env, schema, order=order)
    assert result.original_env == env
