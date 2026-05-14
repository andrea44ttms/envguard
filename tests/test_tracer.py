"""Tests for envguard.tracer."""
from __future__ import annotations

import pytest

from envguard.tracer import trace_env, TraceResult, VarTrace, TraceEntry


@pytest.fixture
def base_source():
    return ("base.env", {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "dev"})


@pytest.fixture
def override_source():
    return ("override.env", {"DB_HOST": "prod-db.example.com", "SECRET_KEY": "abc123"})


def test_single_source_produces_all_active(base_source):
    result = trace_env([base_source])
    assert isinstance(result, TraceResult)
    for key in ["DB_HOST", "DB_PORT", "APP_ENV"]:
        trace = result.get(key)
        assert trace is not None
        assert trace.active_source == "base.env"
        assert trace.active_value is not None


def test_higher_priority_source_wins(base_source, override_source):
    result = trace_env([base_source, override_source])
    trace = result.get("DB_HOST")
    assert trace is not None
    assert trace.active_source == "override.env"
    assert trace.active_value == "prod-db.example.com"


def test_lower_priority_entry_is_marked_overridden(base_source, override_source):
    result = trace_env([base_source, override_source])
    trace = result.get("DB_HOST")
    overridden = [e for e in trace.entries if e.overridden_by is not None]
    assert len(overridden) == 1
    assert overridden[0].source == "base.env"
    assert overridden[0].overridden_by == "override.env"


def test_key_only_in_higher_source_has_no_override(base_source, override_source):
    result = trace_env([base_source, override_source])
    trace = result.get("SECRET_KEY")
    assert trace is not None
    assert len(trace.entries) == 1
    assert trace.entries[0].overridden_by is None


def test_key_only_in_lower_source_is_active_when_not_overridden(base_source, override_source):
    result = trace_env([base_source, override_source])
    trace = result.get("APP_ENV")
    assert trace.active_source == "base.env"
    assert trace.active_value == "dev"


def test_all_keys_returns_sorted_list(base_source, override_source):
    result = trace_env([base_source, override_source])
    keys = result.all_keys
    assert keys == sorted(keys)
    assert "DB_HOST" in keys
    assert "SECRET_KEY" in keys


def test_empty_sources_returns_empty_result():
    result = trace_env([])
    assert result.all_keys == []


def test_str_output_contains_key(base_source):
    result = trace_env([base_source])
    output = str(result)
    assert "DB_HOST" in output
    assert "DB_PORT" in output


def test_var_trace_str_contains_source_and_value(base_source):
    result = trace_env([base_source])
    trace = result.get("DB_HOST")
    s = str(trace)
    assert "base.env" in s
    assert "localhost" in s
    assert "(active)" in s


def test_three_sources_correct_winner():
    s1 = ("defaults.env", {"X": "1"})
    s2 = ("staging.env", {"X": "2"})
    s3 = ("prod.env", {"X": "3"})
    result = trace_env([s1, s2, s3])
    trace = result.get("X")
    assert trace.active_value == "3"
    assert trace.active_source == "prod.env"
    overridden = [e for e in trace.entries if e.overridden_by is not None]
    assert len(overridden) == 2
