"""Tests for envguard.cli_linter."""
from __future__ import annotations

import os
import textwrap

import pytest

from envguard.cli_linter import cmd_lint
from envguard.schema import EnvSchema, EnvVarSchema, EnvVarType


@pytest.fixture()
def env_file(tmp_path):
    """Return a helper that writes an env file and gives back its path."""
    def _write(content: str) -> str:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content))
        return str(p)
    return _write


@pytest.fixture()
def simple_schema() -> EnvSchema:
    s = EnvSchema()
    s.add(EnvVarSchema("APP_ENV", EnvVarType.STRING, required=True))
    s.add(EnvVarSchema("PORT", EnvVarType.INTEGER, required=True))
    return s


def test_clean_env_returns_0(env_file, simple_schema):
    path = env_file("APP_ENV=production\nPORT=8080\n")
    assert cmd_lint(path, schema=simple_schema) == 0


def test_undeclared_key_returns_0_no_errors(env_file, simple_schema):
    # Undeclared keys are warnings, not errors — exit code should still be 0
    path = env_file("APP_ENV=dev\nPORT=8080\nEXTRA=oops\n")
    assert cmd_lint(path, schema=simple_schema) == 0


def test_missing_file_returns_2(tmp_path, simple_schema):
    missing = str(tmp_path / "nonexistent.env")
    assert cmd_lint(missing, schema=simple_schema) == 2


def test_json_format_output(env_file, simple_schema, capsys):
    path = env_file("APP_ENV=dev\nPORT=8080\nUNKNOWN=x\n")
    cmd_lint(path, schema=simple_schema, fmt="json")
    captured = capsys.readouterr().out
    import json
    data = json.loads(captured)
    assert isinstance(data, list)


def test_text_format_output(env_file, simple_schema, capsys):
    path = env_file("APP_ENV=dev\nPORT=8080\n")
    cmd_lint(path, schema=simple_schema, fmt="text")
    captured = capsys.readouterr().out
    assert isinstance(captured, str)


def test_demo_schema_used_when_no_schema_provided(env_file):
    path = env_file("APP_ENV=dev\nPORT=8080\nDEBUG=false\nSECRET_KEY=abc\n")
    # Should not raise; uses built-in demo schema
    result = cmd_lint(path)
    assert result in (0, 1)
