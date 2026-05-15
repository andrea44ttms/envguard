"""Tests for envguard.cli_digester."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envguard.cli_digester import _build_arg_parser, cmd_digest
from envguard.digester import digest_env


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("APP_ENV=production\nDB_HOST=localhost\n")
    return p


def _args(env_file: Path, **kwargs):
    parser = _build_arg_parser()
    argv = [str(env_file)]
    for k, v in kwargs.items():
        if k == "as_json" and v:
            argv.append("--json")
        elif k == "algorithm":
            argv += ["--algorithm", v]
        elif k == "previous":
            argv += ["--previous", v]
    return parser.parse_args(argv)


def test_cmd_digest_returns_0_on_valid_file(env_file: Path, capsys):
    assert cmd_digest(_args(env_file)) == 0


def test_cmd_digest_returns_2_on_missing_file(tmp_path: Path):
    missing = tmp_path / "ghost.env"
    assert cmd_digest(_args(missing)) == 2


def test_cmd_digest_text_output_contains_digest(env_file: Path, capsys):
    cmd_digest(_args(env_file))
    out = capsys.readouterr().out
    assert "digest" in out


def test_cmd_digest_json_output_is_valid(env_file: Path, capsys):
    cmd_digest(_args(env_file, as_json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "digest" in data
    assert "algorithm" in data
    assert data["algorithm"] == "sha256"


def test_cmd_digest_md5_algorithm(env_file: Path, capsys):
    cmd_digest(_args(env_file, algorithm="md5", as_json=True))
    data = json.loads(capsys.readouterr().out)
    assert data["algorithm"] == "md5"
    assert len(data["digest"]) == 32


def test_cmd_digest_returns_1_when_changed(env_file: Path):
    old_digest = "deadbeef" * 8
    rc = cmd_digest(_args(env_file, previous=old_digest))
    assert rc == 1


def test_cmd_digest_returns_0_when_unchanged(env_file: Path):
    from envguard.loader import load_env_file
    env = load_env_file(env_file)
    current = digest_env(env).digest
    rc = cmd_digest(_args(env_file, previous=current))
    assert rc == 0


def test_cmd_digest_json_includes_changed_field(env_file: Path, capsys):
    cmd_digest(_args(env_file, previous="deadbeef" * 8, as_json=True))
    data = json.loads(capsys.readouterr().out)
    assert data["changed"] is True
