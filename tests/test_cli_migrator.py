"""Tests for envguard.cli_migrator."""
import argparse
import json
import pytest
from pathlib import Path

from envguard.cli_migrator import cmd_migrate


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nOLD_KEY=value\nAPP_ENV=dev\n")
    return p


def _args(file, rename=None, patch=None, fmt="text"):
    ns = argparse.Namespace()
    ns.file = str(file)
    ns.rename = rename or []
    ns.patch = patch or []
    ns.format = fmt
    return ns


def test_cmd_migrate_returns_0_on_valid_file(env_file):
    assert cmd_migrate(_args(env_file)) == 0


def test_cmd_migrate_returns_2_on_missing_file(tmp_path):
    assert cmd_migrate(_args(tmp_path / "no.env")) == 2


def test_cmd_migrate_rename_reflected_in_output(env_file, capsys):
    cmd_migrate(_args(env_file, rename=["OLD_KEY:NEW_KEY"]))
    out = capsys.readouterr().out
    assert "NEW_KEY" in out


def test_cmd_migrate_patch_reflected_in_output(env_file, capsys):
    cmd_migrate(_args(env_file, patch=["APP_ENV=production"]))
    out = capsys.readouterr().out
    assert "production" in out


def test_cmd_migrate_json_format(env_file, capsys):
    cmd_migrate(_args(env_file, rename=["OLD_KEY:NEW_KEY"], fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "migrated" in data
    assert data["apply_count"] == 1
    assert "NEW_KEY" in data["migrated"]


def test_cmd_migrate_dotenv_format(env_file, capsys):
    cmd_migrate(_args(env_file, fmt="dotenv"))
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    assert all("=" in line for line in lines)


def test_cmd_migrate_skip_missing_rename(env_file, capsys):
    cmd_migrate(_args(env_file, rename=["NONEXISTENT:NEWNAME"]))
    out = capsys.readouterr().out
    assert "0 applied" in out or "skipped" in out
