"""Tests for envguard.cli_grouper module."""
import os
import pytest
from pathlib import Path
from envguard.cli_grouper import cmd_group
import argparse


@pytest.fixture
def env_file(tmp_path):
    return tmp_path / ".env"


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def _args(env_file, separator="_", min_prefix=2, use_demo_schema=False):
    return argparse.Namespace(
        env_file=str(env_file),
        separator=separator,
        min_prefix=min_prefix,
        use_demo_schema=use_demo_schema,
    )


def test_cmd_group_returns_0_on_valid_file(env_file):
    _write(env_file, "DB_HOST=localhost\nDB_PORT=5432\nAPP_DEBUG=true\n")
    assert cmd_group(_args(env_file)) == 0


def test_cmd_group_returns_2_on_missing_file(tmp_path):
    missing = tmp_path / "missing.env"
    assert cmd_group(_args(missing)) == 2


def test_cmd_group_with_demo_schema(env_file):
    _write(env_file, "DB_HOST=localhost\nDB_PORT=5432\nDB_NAME=mydb\nAWS_ACCESS_KEY=abc\n")
    assert cmd_group(_args(env_file, use_demo_schema=True)) == 0


def test_cmd_group_output_contains_group_info(env_file, capsys):
    _write(env_file, "DB_HOST=localhost\nDB_PORT=5432\nAWS_KEY=abc\n")
    cmd_group(_args(env_file))
    captured = capsys.readouterr()
    assert "Groups found" in captured.out
    assert "DB" in captured.out


def test_cmd_group_custom_separator(env_file):
    _write(env_file, "DB.HOST=localhost\nDB.PORT=5432\n")
    assert cmd_group(_args(env_file, separator=".")) == 0
