"""Tests for envguard.validator_chain."""
import pytest
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType
from envguard.validator_chain import ChainStep, ChainResult, run_chain


@pytest.fixture()
def schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema("APP_ENV", type=EnvVarType.STRING, required=True))
    s.add(EnvVarSchema("PORT", type=EnvVarType.INTEGER, required=True))
    return s


def _step(name: str, schema: EnvSchema, env: dict) -> ChainStep:
    return ChainStep(name=name, schema=schema, env=env)


def test_all_valid_steps_produce_ok_chain(schema):
    env = {"APP_ENV": "production", "PORT": "8080"}
    steps = [_step("s1", schema, env), _step("s2", schema, env)]
    result = run_chain(steps)
    assert result.ok is True
    assert result.total_errors == 0
    assert result.failed_steps == []


def test_single_invalid_step_fails_chain(schema):
    good = {"APP_ENV": "production", "PORT": "8080"}
    bad = {"APP_ENV": "staging"}  # missing PORT
    steps = [_step("good", schema, good), _step("bad", schema, bad)]
    result = run_chain(steps)
    assert result.ok is False
    assert "bad" in result.failed_steps
    assert result.total_errors >= 1


def test_errors_for_returns_correct_step_errors(schema):
    bad = {"APP_ENV": "staging"}  # missing PORT
    steps = [_step("only", schema, bad)]
    result = run_chain(steps)
    errors = result.errors_for("only")
    assert len(errors) > 0
    assert any("PORT" in str(e) for e in errors)


def test_errors_for_unknown_step_returns_empty(schema):
    steps = [_step("s1", schema, {"APP_ENV": "x", "PORT": "1"})]
    result = run_chain(steps)
    assert result.errors_for("nonexistent") == []


def test_stop_on_first_failure_halts_chain(schema):
    bad = {}  # all missing
    good = {"APP_ENV": "x", "PORT": "9"}
    steps = [_step("fail", schema, bad), _step("pass", schema, good)]
    result = run_chain(steps, stop_on_first_failure=True)
    # Only the first step should have been executed
    assert len(result.steps) == 1
    assert result.steps[0][0] == "fail"


def test_stop_on_first_failure_false_runs_all(schema):
    bad = {}
    steps = [_step("f1", schema, bad), _step("f2", schema, bad)]
    result = run_chain(steps, stop_on_first_failure=False)
    assert len(result.steps) == 2


def test_chain_result_str_contains_step_names(schema):
    env = {"APP_ENV": "dev", "PORT": "3000"}
    steps = [_step("alpha", schema, env)]
    result = run_chain(steps)
    text = str(result)
    assert "alpha" in text
    assert "OK" in text


def test_empty_steps_produces_ok_chain():
    result = run_chain([])
    assert result.ok is True
    assert result.total_errors == 0
    assert result.failed_steps == []
