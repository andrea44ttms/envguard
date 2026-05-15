"""Tests for envguard.cli_expirer."""
import json
from pathlib import Path

import pytest

from envguard.cli_expirer import _build_arg_parser, cmd_expiry


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "CERT_EXPIRY=2020-01-01\n"
        "TOKEN_EXPIRY=2099-12-31\n"
    )
    return p


def _args(env_file, keys, fmt="text", ref_date=None):
    parser = _build_arg_parser()
    argv = [str(env_file), "--keys"] + keys
    if ref_date:
        argv += ["--ref-date", ref_date]
    argv += ["--format", fmt]
    return parser.parse_args(argv)


def test_expired_key_returns_1(env_file):
    args = _args(env_file, ["CERT_EXPIRY"], ref_date="2024-06-15")
    assert cmd_expiry(args) == 1


def test_valid_key_returns_0(env_file):
    args = _args(env_file, ["TOKEN_EXPIRY"], ref_date="2024-06-15")
    assert cmd_expiry(args) == 0


def test_missing_file_returns_2(tmp_path):
    args = _args(tmp_path / "missing.env", ["CERT_EXPIRY"])
    assert cmd_expiry(args) == 2


def test_invalid_ref_date_returns_2(env_file, capsys):
    parser = _build_arg_parser()
    args = parser.parse_args(
        [str(env_file), "--keys", "CERT_EXPIRY", "--ref-date", "bad-date"]
    )
    rc = cmd_expiry(args)
    assert rc == 2
    captured = capsys.readouterr()
    assert "invalid ref-date" in captured.err


def test_json_output_structure(env_file, capsys):
    args = _args(env_file, ["CERT_EXPIRY", "TOKEN_EXPIRY"], fmt="json", ref_date="2024-06-15")
    cmd_expiry(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "expired_count" in data
    assert "entries" in data
    assert "unparseable" in data


def test_json_expired_count_correct(env_file, capsys):
    args = _args(env_file, ["CERT_EXPIRY", "TOKEN_EXPIRY"], fmt="json", ref_date="2024-06-15")
    cmd_expiry(args)
    data = json.loads(capsys.readouterr().out)
    assert data["expired_count"] == 1
