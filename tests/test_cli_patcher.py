"""Tests for envguard.cli_patcher."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envguard.cli_patcher import cmd_patch


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_HOST=localhost\nAPP_PORT=8000\nDEBUG=true\n")
    return p


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"file": "", "set": None, "remove": None, "write": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_patch_returns_0_on_valid_file(env_file):
    rc = cmd_patch(_args(file=str(env_file)))
    assert rc == 0


def test_cmd_patch_returns_2_on_missing_file(tmp_path):
    rc = cmd_patch(_args(file=str(tmp_path / "missing.env")))
    assert rc == 2


def test_cmd_patch_prints_patched_lines(env_file, capsys):
    rc = cmd_patch(_args(file=str(env_file), set=["APP_PORT=9000"]))
    assert rc == 0
    out = capsys.readouterr().out
    assert "APP_PORT=9000" in out


def test_cmd_patch_write_modifies_file(env_file):
    rc = cmd_patch(_args(file=str(env_file), set=["APP_PORT=9999"], write=True))
    assert rc == 0
    content = env_file.read_text()
    assert "APP_PORT=9999" in content


def test_cmd_patch_remove_key(env_file):
    rc = cmd_patch(_args(file=str(env_file), remove=["DEBUG"], write=True))
    assert rc == 0
    content = env_file.read_text()
    assert "DEBUG" not in content


def test_cmd_patch_add_new_key(env_file, capsys):
    rc = cmd_patch(_args(file=str(env_file), set=["NEW_KEY=hello"]))
    assert rc == 0
    out = capsys.readouterr().out
    assert "NEW_KEY=hello" in out
