"""Tests for envguard.cli_inspector."""
import json
import os
import pytest
from pathlib import Path
from envguard.cli_inspector import cmd_inspect, _build_arg_parser


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DATABASE_URL=postgres://localhost/mydb\n"
        "PORT=5432\n"
        "DEBUG=true\n"
        "API_SECRET=topsecret\n"
    )
    return p


def _args(env_file, fmt="text", keys=None):
    parser = _build_arg_parser()
    cmd = [str(env_file), "--format", fmt]
    if keys:
        cmd += ["--keys"] + keys
    return parser.parse_args(cmd)


def test_cmd_inspect_returns_0_on_valid_file(env_file):
    args = _args(env_file)
    assert cmd_inspect(args) == 0


def test_cmd_inspect_returns_2_on_missing_file(tmp_path):
    args = _args(tmp_path / "missing.env")
    assert cmd_inspect(args) == 2


def test_cmd_inspect_text_output_contains_key(env_file, capsys):
    args = _args(env_file)
    cmd_inspect(args)
    captured = capsys.readouterr()
    assert "DATABASE_URL" in captured.out


def test_cmd_inspect_json_output_is_valid(env_file, capsys):
    args = _args(env_file, fmt="json")
    cmd_inspect(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) > 0


def test_cmd_inspect_json_contains_inferred_type(env_file, capsys):
    args = _args(env_file, fmt="json")
    cmd_inspect(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    port_entry = next((d for d in data if d["key"] == "PORT"), None)
    assert port_entry is not None
    assert port_entry["inferred_type"] == "integer"


def test_cmd_inspect_key_filter_limits_output(env_file, capsys):
    args = _args(env_file, keys=["PORT"])
    cmd_inspect(args)
    captured = capsys.readouterr()
    assert "PORT" in captured.out
    assert "DATABASE_URL" not in captured.out


def test_cmd_inspect_sensitive_flagged_in_json(env_file, capsys):
    args = _args(env_file, fmt="json")
    cmd_inspect(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    secret_entry = next((d for d in data if d["key"] == "API_SECRET"), None)
    assert secret_entry is not None
    assert secret_entry["is_sensitive"] is True
