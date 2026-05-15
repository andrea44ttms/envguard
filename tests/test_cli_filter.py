"""Tests for envguard.cli_filter."""
from __future__ import annotations

import json
import os

import pytest

from envguard.cli_filter import cmd_filter


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "REDIS_URL=redis://localhost\n"
        "APP_DEBUG=true\n"
    )
    return str(p)


class _Args:
    def __init__(self, env_file, patterns=None, format="text", name="cli"):
        self.env_file = env_file
        self.patterns = patterns
        self.format = format
        self.name = name


def test_cmd_filter_returns_0_on_valid_file(env_file):
    args = _Args(env_file)
    assert cmd_filter(args) == 0


def test_cmd_filter_returns_2_on_missing_file():
    args = _Args("/nonexistent/.env")
    assert cmd_filter(args) == 2


def test_cmd_filter_text_output_contains_matched_key(env_file, capsys):
    args = _Args(env_file, patterns=["DB_*"])
    cmd_filter(args)
    out = capsys.readouterr().out
    assert "DB_HOST" in out


def test_cmd_filter_json_output_structure(env_file, capsys):
    args = _Args(env_file, patterns=["DB_*"], format="json")
    cmd_filter(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "matched" in data
    assert "excluded" in data
    assert "DB_HOST" in data["matched"]


def test_cmd_filter_dotenv_output(env_file, capsys):
    args = _Args(env_file, patterns=["REDIS_*"], format="dotenv")
    cmd_filter(args)
    out = capsys.readouterr().out
    assert "REDIS_URL=redis://localhost" in out


def test_cmd_filter_no_pattern_returns_all_keys(env_file, capsys):
    args = _Args(env_file, format="json")
    cmd_filter(args)
    data = json.loads(capsys.readouterr().out)
    assert len(data["matched"]) == 4
