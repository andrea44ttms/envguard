"""Tests for envguard.cli_profiler."""

import json
import os
import pytest

from envguard.cli_profiler import cmd_profile
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture()
def env_file(tmp_path):
    def _write(contents: str):
        p = tmp_path / ".env"
        p.write_text(contents)
        return str(p)
    return _write


@pytest.fixture()
def simple_schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema(name="APP_NAME", type=EnvVarType.STRING, required=True))
    s.add(EnvVarSchema(name="SECRET_KEY", type=EnvVarType.STRING, required=True))
    s.add(EnvVarSchema(name="PORT", type=EnvVarType.INTEGER, required=False, default="8080"))
    return s


def test_cmd_profile_returns_0_on_valid(env_file, simple_schema, capsys):
    path = env_file("APP_NAME=myapp\nSECRET_KEY=abc123\n")
    code = cmd_profile(path, schema=simple_schema)
    assert code == 0


def test_cmd_profile_returns_1_on_missing_required(env_file, simple_schema, capsys):
    path = env_file("APP_NAME=myapp\n")  # missing SECRET_KEY
    code = cmd_profile(path, schema=simple_schema)
    assert code == 1


def test_cmd_profile_text_output(env_file, simple_schema, capsys):
    path = env_file("APP_NAME=myapp\nSECRET_KEY=abc123\n")
    cmd_profile(path, fmt="text", schema=simple_schema)
    out = capsys.readouterr().out
    assert "EnvProfile" in out
    assert "health=" in out


def test_cmd_profile_json_output(env_file, simple_schema, capsys):
    path = env_file("APP_NAME=myapp\nSECRET_KEY=abc123\n")
    cmd_profile(path, fmt="json", schema=simple_schema)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "total" in data
    assert "health_score" in data
    assert data["health_score"] == 1.0


def test_cmd_profile_json_includes_error_keys(env_file, simple_schema, capsys):
    path = env_file("APP_NAME=myapp\n")  # missing SECRET_KEY
    cmd_profile(path, fmt="json", schema=simple_schema)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "SECRET_KEY" in data["error_keys"]


def test_cmd_profile_missing_file(capsys):
    code = cmd_profile("/nonexistent/.env")
    assert code == 1
    err = capsys.readouterr().err
    assert "not found" in err.lower()
