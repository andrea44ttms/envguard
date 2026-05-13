"""Tests for envguard.cli_freezer."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from envguard.cli_freezer import cmd_diff, cmd_freeze, cmd_show
from envguard.freezer import freeze_env, save_freeze


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_HOST=localhost\nAPP_PORT=8080\nDB_PASSWORD=s3cr3t\n")
    return p


@pytest.fixture()
def freeze_file(tmp_path: Path, env_file: Path) -> Path:
    from envguard.loader import load_env_file

    env = load_env_file(env_file)
    frozen = freeze_env(env, redact=False)
    dest = tmp_path / "env.freeze.json"
    save_freeze(frozen, dest)
    return dest


def test_cmd_freeze_returns_0_on_valid_file(tmp_path, env_file):
    out = tmp_path / "out.json"
    args = SimpleNamespace(env_file=str(env_file), output=str(out), no_redact=False)
    assert cmd_freeze(args) == 0


def test_cmd_freeze_creates_output_file(tmp_path, env_file):
    out = tmp_path / "out.json"
    args = SimpleNamespace(env_file=str(env_file), output=str(out), no_redact=False)
    cmd_freeze(args)
    assert out.exists()


def test_cmd_freeze_returns_2_on_missing_file(tmp_path):
    args = SimpleNamespace(
        env_file="/nonexistent/.env",
        output=str(tmp_path / "out.json"),
        no_redact=False,
    )
    assert cmd_freeze(args) == 2


def test_cmd_show_returns_0(freeze_file, capsys):
    args = SimpleNamespace(freeze_file=str(freeze_file), json=False)
    assert cmd_show(args) == 0


def test_cmd_show_json_output(freeze_file, capsys):
    args = SimpleNamespace(freeze_file=str(freeze_file), json=True)
    cmd_show(args)
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "values" in parsed


def test_cmd_show_returns_2_on_missing_freeze_file():
    args = SimpleNamespace(freeze_file="/no/such/file.json", json=False)
    assert cmd_show(args) == 2


def test_cmd_diff_returns_0_when_no_changes(freeze_file, env_file):
    args = SimpleNamespace(
        freeze_file=str(freeze_file),
        env_file=str(env_file),
        no_redact=True,
    )
    assert cmd_diff(args) == 0


def test_cmd_diff_returns_1_when_changes_exist(freeze_file, tmp_path):
    changed = tmp_path / "changed.env"
    changed.write_text("APP_HOST=remotehost\nAPP_PORT=9090\nDB_PASSWORD=other\n")
    args = SimpleNamespace(
        freeze_file=str(freeze_file),
        env_file=str(changed),
        no_redact=True,
    )
    assert cmd_diff(args) == 1


def test_cmd_diff_returns_2_on_missing_freeze_file(env_file):
    args = SimpleNamespace(
        freeze_file="/no/such/freeze.json",
        env_file=str(env_file),
        no_redact=False,
    )
    assert cmd_diff(args) == 2
