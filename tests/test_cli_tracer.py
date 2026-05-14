"""Tests for envguard.cli_tracer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envguard.cli_tracer import cmd_trace


@pytest.fixture
def env_file(tmp_path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content)
        return p
    return _write


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"files": [], "key": None, "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_trace_returns_0_on_valid_files(env_file):
    f1 = env_file("base.env", "DB_HOST=localhost\nAPP_ENV=dev\n")
    f2 = env_file("prod.env", "DB_HOST=prod-db\n")
    args = _args(files=[str(f1), str(f2)])
    assert cmd_trace(args) == 0


def test_cmd_trace_returns_2_on_missing_file(env_file):
    args = _args(files=["/nonexistent/path.env"])
    assert cmd_trace(args) == 2


def test_cmd_trace_single_key_filter(env_file, capsys):
    f1 = env_file("base.env", "DB_HOST=localhost\nAPP_ENV=dev\n")
    args = _args(files=[str(f1)], key="DB_HOST")
    rc = cmd_trace(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "APP_ENV" not in out


def test_cmd_trace_missing_key_returns_1(env_file):
    f1 = env_file("base.env", "DB_HOST=localhost\n")
    args = _args(files=[str(f1)], key="MISSING_KEY")
    assert cmd_trace(args) == 1


def test_cmd_trace_json_output_structure(env_file, capsys):
    f1 = env_file("base.env", "DB_HOST=localhost\n")
    f2 = env_file("prod.env", "DB_HOST=prod-db\n")
    args = _args(files=[str(f1), str(f2)], format="json")
    rc = cmd_trace(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "DB_HOST" in data
    entry = data["DB_HOST"]
    assert entry["active_value"] == "prod-db"
    assert entry["active_source"] == "prod.env"
    assert isinstance(entry["history"], list)
    assert len(entry["history"]) == 2


def test_cmd_trace_text_shows_active(env_file, capsys):
    f1 = env_file("only.env", "SECRET=mysecret\n")
    args = _args(files=[str(f1)])
    cmd_trace(args)
    out = capsys.readouterr().out
    assert "(active)" in out
