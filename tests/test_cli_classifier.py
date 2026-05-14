"""Tests for envguard.cli_classifier."""
import json
import argparse
import pytest
from pathlib import Path

from envguard.cli_classifier import cmd_classify


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "DATABASE_URL=postgres://localhost/db\n"
        "SECRET_KEY=mysecret\n"
        "PORT=8080\n"
        "FOOBAR=baz\n"
    )
    return p


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"format": "text", "category": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_classify_returns_0_on_valid_file(env_file, capsys):
    rc = cmd_classify(_args(env_file=str(env_file)))
    assert rc == 0


def test_cmd_classify_returns_2_on_missing_file(tmp_path):
    rc = cmd_classify(_args(env_file=str(tmp_path / "missing.env")))
    assert rc == 2


def test_cmd_classify_text_output_contains_categories(env_file, capsys):
    cmd_classify(_args(env_file=str(env_file)))
    out = capsys.readouterr().out
    assert "[database]" in out
    assert "[security]" in out
    assert "[networking]" in out


def test_cmd_classify_json_output_is_valid(env_file, capsys):
    cmd_classify(_args(env_file=str(env_file), format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "database" in data
    assert "DATABASE_URL" in data["database"]


def test_cmd_classify_filter_by_category(env_file, capsys):
    cmd_classify(_args(env_file=str(env_file), category="security"))
    out = capsys.readouterr().out
    assert "SECRET_KEY" in out
    assert "PORT" not in out


def test_cmd_classify_json_filter_by_category(env_file, capsys):
    cmd_classify(_args(env_file=str(env_file), format="json", category="security"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "security" in data
    assert "SECRET_KEY" in data["security"]
